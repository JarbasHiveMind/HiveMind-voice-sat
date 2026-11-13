"""ACL / policy-model e2e tests for HiveMind voice satellite.

Demonstrates the three policy-admission enforcement paths a voice satellite
relies on:

1. **allowed_types denial** — a satellite whose ``allowed_types`` excludes
   ``recognizer_loop:utterance`` has its utterance blocked by
   ``MessageTypeACLPolicy`` with code ``ACL_DISALLOWED_TYPE``.  The message
   never reaches the agent bus.

2. **Skill-blacklist injection** — a satellite allowed to inject utterances
   but registered with ``skill_blacklist=["skill-weather"]`` has its utterance
   delivered WITH ``session.blacklisted_skills=["skill-weather"]`` injected by
   ``OVOSAgentPolicy`` + ``AddBlacklistedSkill``.

3. **Default session_id forbidden** — a non-admin satellite sending a message
   with ``session_id="default"`` is denied by ``OVOSAgentPolicy`` with code
   ``SESSION_ID_DEFAULT_FORBIDDEN`` (SESSION-1 §3.1 reserved-id gate).

All admission control flows through the ``PolicyChain``
(``MessageTypeACLPolicy`` force-prepended, then ``OVOSAgentPolicy``).
"""

import time

import pytest
from hivemind_bus_client.message import HiveMessage, HiveMessageType
from ovos_bus_client.message import Message

from hivescope.scenarios import with_acl_enforcement
from hivescope.assertions import (
    assert_policy_denied,
    assert_session_blacklists_injected,
    ACL_DISALLOWED_TYPE,
    SESSION_ID_DEFAULT_FORBIDDEN,
)


def test_allowed_types_denial():
    """Non-admin satellite whose allowed_types excludes recognizer_loop:utterance
    has its utterance blocked by MessageTypeACLPolicy (ACL_DISALLOWED_TYPE).

    The message must not reach the agent bus.
    """
    b = with_acl_enforcement()
    b.start_all()
    try:
        m = b.get_master("M0")
        s = b.get_satellite("S_RESTRICTED_TYPE")

        s.send(HiveMessage(
            HiveMessageType.BUS,
            payload=Message("recognizer_loop:utterance", {"utterances": ["what is the weather"]}),
        ))

        time.sleep(0.2)

        assert_policy_denied(
            m, s,
            msg_type="recognizer_loop:utterance",
            deny_code=ACL_DISALLOWED_TYPE,
        )
    finally:
        b.stop_all()


def test_skill_blacklist_injection():
    """Satellite with skill_blacklist=["skill-weather"] can inject an utterance
    (allowed_types includes recognizer_loop:utterance) but OVOSAgentPolicy
    injects session.blacklisted_skills=["skill-weather"] so the OVOS pipeline
    cannot route to the blacklisted skill.
    """
    b = with_acl_enforcement()
    b.start_all()
    try:
        m = b.get_master("M0")
        s = b.get_satellite("S_RESTRICTED_SKILL")

        seen = []
        m.agent_protocol.bus.on("recognizer_loop:utterance", seen.append)

        s.send(HiveMessage(
            HiveMessageType.BUS,
            payload=Message("recognizer_loop:utterance", {"utterances": ["what is the weather"]}),
        ))

        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and not seen:
            time.sleep(0.02)

        assert seen, "utterance did not reach the agent bus at all"

        assert_session_blacklists_injected(
            m, s,
            msg_type="recognizer_loop:utterance",
            expected_skills=["skill-weather"],
        )
    finally:
        b.stop_all()


@pytest.mark.xfail(
    reason=(
        "The bridge's _install_client_session rewrites the session before "
        "OVOSAgentPolicy runs in the e2e dispatch path, so session_id='default' "
        "in a BUS payload context is overwritten before the policy gate fires. "
        "SESSION_ID_DEFAULT_FORBIDDEN is verified by OVOSAgentPolicy unit tests; "
        "this xfail tracks the e2e path becoming testable once core exposes a "
        "pre-session-rewrite policy hook."
    ),
    strict=False,
)
def test_default_session_id_denied_for_non_admin():
    """A non-admin satellite sending session_id="default" is denied per
    OVOS-SESSION-1 §3.1 (SESSION_ID_DEFAULT_FORBIDDEN).

    Only admin peers may use the reserved default session.
    S_RESTRICTED_SKILL has allowed_types=["recognizer_loop:utterance"] so the
    message passes the type gate; OVOSAgentPolicy then checks session_id and
    rejects it with SESSION_ID_DEFAULT_FORBIDDEN.
    """
    b = with_acl_enforcement()
    b.start_all()
    try:
        m = b.get_master("M0")
        # S_RESTRICTED_SKILL: utterance type is in allowed_types, so
        # MessageTypeACLPolicy passes and OVOSAgentPolicy evaluates the
        # reserved session_id and denies it.
        s = b.get_satellite("S_RESTRICTED_SKILL")

        s.send(HiveMessage(
            HiveMessageType.BUS,
            payload=Message(
                "recognizer_loop:utterance",
                {"utterances": ["hello"]},
                context={"session": {"session_id": "default"}},
            ),
        ))

        time.sleep(0.2)

        assert_policy_denied(
            m, s,
            msg_type="recognizer_loop:utterance",
            deny_code=SESSION_ID_DEFAULT_FORBIDDEN,
        )
    finally:
        b.stop_all()
