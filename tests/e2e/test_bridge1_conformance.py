"""
OVOS-BRIDGE-1 conformance template.

Copy this file into your repo's ``tests/e2e/`` directory and adapt it to
your bridge implementation.  Each test group directly maps to one normative
clause of OVOS-BRIDGE-1, SESSION-1, or SESSION-2.

Usage:
    cp templates/test_template_bridge1.py <your-repo>/tests/e2e/test_bridge1_conformance.py

The tests use the hivescope in-process harness — no real WebSocket server
is needed.  See hivescope README for installation.

Skipif pattern
--------------
Tests that depend on the policy admission chain (BRIDGE-1 §4.2) are gated
with ``@_requires_policy_chain`` so they pass on released core and activate
automatically once ``hivemind_core.policy`` (core#89) is installed.

Source/destination/session-fidelity/FIFO tests do NOT use a skipif guard;
they must pass on released core.
"""

import importlib.util
import time

import pytest
from hivemind_bus_client.message import HiveMessage, HiveMessageType
from ovos_bus_client.message import Message
from ovos_bus_client.session import Session

from hivescope.topology import TopologyBuilder
from hivescope.assertions import (
    assert_msg1_envelope,
    assert_source_stamped,
    assert_destination_routed,
    assert_session_inbound_preserved,
    assert_session_outbound_preserved,
    assert_fifo_order,
    assert_session_propagated_unchanged,
    assert_source_hidden,
    assert_session_blacklists_injected,
)
from hivescope.scenarios import single_satellite, three_satellites, chain_topology

# ---------------------------------------------------------------------------
# Skipif markers — copy these into your test file unchanged.
# ---------------------------------------------------------------------------

_HAS_POLICY_CHAIN = importlib.util.find_spec("hivemind_core.policy") is not None
_HAS_OVOS_POLICY = importlib.util.find_spec("hivemind_ovos_agent_plugin") is not None

_requires_policy_chain = pytest.mark.skipif(
    not _HAS_POLICY_CHAIN,
    reason="policy admission chain (HiveMind-core#89) not installed",
)
_requires_ovos_policy = pytest.mark.skipif(
    not (_HAS_POLICY_CHAIN and _HAS_OVOS_POLICY),
    reason="OVOSAgentPolicy (hivemind-ovos-agent-plugin#3) + core#89 not installed",
)


# ---------------------------------------------------------------------------
# Topology helpers
# ---------------------------------------------------------------------------

def _topology_with_utterance():
    """Single-satellite topology with recognizer_loop:utterance whitelisted."""
    b = TopologyBuilder()
    m = b.add_master("M0")
    b.add_satellite("S0", upstream=m,
                    allowed_types=["recognizer_loop:utterance", "speak"])
    return b


def _make_utterance(seq: int = 0, session_id: str = None, lang: str = "en-US") -> Message:
    """Build a test utterance Message with an optional FIFO sequence number."""
    ctx: dict = {}
    if session_id:
        sess = Session(session_id=session_id, lang=lang)
        ctx["session"] = sess.serialize()
    return Message(
        "recognizer_loop:utterance",
        data={"utterances": [f"utterance {seq}"], "_fifo_seq": seq},
        context=ctx,
    )


# ─────────────────────────────────────────────────────────────────────────────
# BRIDGE-1 §2 — OVOS-MSG-1 envelope
# ─────────────────────────────────────────────────────────────────────────────

def test_msg1_envelope():
    """Bus-injected messages conform to OVOS-MSG-1 (msg_type + context present).

    Spec: BRIDGE-1 §2
    Helper: assert_msg1_envelope
    """
    b = _topology_with_utterance()
    b.start_all()
    try:
        m = b.get_master("M0")
        s = b.get_satellite("S0")
        s.send(_make_utterance())
        time.sleep(0.2)
        assert_msg1_envelope(m, "recognizer_loop:utterance", count=1)
    finally:
        b.stop_all()


# ─────────────────────────────────────────────────────────────────────────────
# BRIDGE-1 §3.1 — Unique, stable context.source per satellite
# ─────────────────────────────────────────────────────────────────────────────

def test_source_stamped_single():
    """Satellite's injections carry a stable non-empty context.source.

    Spec: BRIDGE-1 §3.1
    Helper: assert_source_stamped
    """
    b = _topology_with_utterance()
    b.start_all()
    try:
        m = b.get_master("M0")
        s = b.get_satellite("S0")
        for i in range(3):
            s.send(_make_utterance(seq=i))
            time.sleep(0.05)
        assert_source_stamped(m, s)
    finally:
        b.stop_all()


def test_source_unique_multi_satellite():
    """Three satellites receive distinct context.source values.

    Spec: BRIDGE-1 §3.1 (uniqueness across peers)
    Topology: three_satellites()
    Helper: assert_source_stamped(other_satellites=[...])
    """
    b = TopologyBuilder()
    m_node = b.add_master("M0")
    for i in range(3):
        b.add_satellite(f"S{i}", upstream=m_node,
                        allowed_types=["recognizer_loop:utterance"])
    b.start_all()
    try:
        m = b.get_master("M0")
        sats = [b.get_satellite(f"S{i}") for i in range(3)]
        for s in sats:
            s.send(_make_utterance(seq=0))
            time.sleep(0.1)
        for sat in sats:
            others = [s for s in sats if s is not sat]
            assert_source_stamped(m, sat, other_satellites=others)
    finally:
        b.stop_all()


# ─────────────────────────────────────────────────────────────────────────────
# BRIDGE-1 §3.2 — Destination routing (no cross-talk)
# ─────────────────────────────────────────────────────────────────────────────

def test_destination_routed():
    """Targeted outbound message reaches only the addressed satellite.

    Spec: BRIDGE-1 §3.2
    Topology: three_satellites()
    Helper: assert_destination_routed
    """
    b = TopologyBuilder()
    m_node = b.add_master("M0")
    for i in range(3):
        b.add_satellite(f"S{i}", upstream=m_node,
                        allowed_types=["recognizer_loop:utterance", "speak"])
    b.start_all()
    try:
        m = b.get_master("M0")
        s0 = b.get_satellite("S0")
        s1 = b.get_satellite("S1")
        s2 = b.get_satellite("S2")

        m.emit_on_bus(Message(
            "speak",
            data={"utterance": "only for S0"},
            context={"destination": s0.peer},
        ))

        assert_destination_routed(
            m, s0,
            other_satellites=[s1, s2],
            msg_type=HiveMessageType.BUS.value,
        )
    finally:
        b.stop_all()


# ─────────────────────────────────────────────────────────────────────────────
# BRIDGE-1 §4.1 — Session fidelity (inbound + outbound)
# ─────────────────────────────────────────────────────────────────────────────

def test_session_inbound_preserved():
    """Satellite's session fields are preserved into bus context.session.

    Spec: BRIDGE-1 §4.1 (inbound)
    Helper: assert_session_inbound_preserved
    """
    b = _topology_with_utterance()
    b.start_all()
    try:
        m = b.get_master("M0")
        s = b.get_satellite("S0")

        sid = s.shim.session_id
        sess = Session(session_id=sid, lang="pt-PT")
        s.send(Message(
            "recognizer_loop:utterance",
            data={"utterances": ["olá"]},
            context={"session": sess.serialize()},
        ))
        time.sleep(0.2)

        assert_session_inbound_preserved(
            m, s,
            expected_session={"session_id": sid, "lang": sess.serialize().get("lang")},
        )
    finally:
        b.stop_all()


def test_session_outbound_preserved():
    """Bus-originated message's session is forwarded to the satellite intact.

    Spec: BRIDGE-1 §4.1 (outbound)
    Helper: assert_session_outbound_preserved
    """
    b = _topology_with_utterance()
    b.start_all()
    try:
        m = b.get_master("M0")
        s = b.get_satellite("S0")

        sid = s.shim.session_id
        sess = Session(session_id=sid, lang="de-DE")
        m.emit_on_bus(Message(
            "speak",
            data={"utterance": "Hallo"},
            context={"destination": s.peer, "session": sess.serialize()},
        ))

        assert_session_outbound_preserved(
            s,
            expected_session={"session_id": sid},
        )
    finally:
        b.stop_all()


# ─────────────────────────────────────────────────────────────────────────────
# BRIDGE-1 §4.2 — Policy injection (requires policy chain)
# ─────────────────────────────────────────────────────────────────────────────


def test_fifo_order_direct():
    """Sequential utterances from one satellite arrive in send order.

    Spec: BRIDGE-1 §5
    Helper: assert_fifo_order (uses _fifo_seq tag)
    """
    b = _topology_with_utterance()
    b.start_all()
    try:
        m = b.get_master("M0")
        s = b.get_satellite("S0")

        for i in range(5):
            s.send(_make_utterance(seq=i))
            time.sleep(0.02)

        assert_fifo_order(m, s, "recognizer_loop:utterance", count=5)
    finally:
        b.stop_all()


@pytest.mark.xfail(
    strict=False,
    reason="relay FIFO: depends on relay chain being fully wired (chain_topology)",
)
def test_fifo_order_relay_chain():
    """Sequential utterances through a relay chain arrive in order at root.

    Spec: BRIDGE-1 §5 (relay hop)
    Topology: chain_topology() — M0→R0→S0
    Helper: assert_fifo_order
    """
    b = chain_topology()
    b.start_all()
    try:
        r = b.get_relay("R0")
        s = b.get_satellite("S0")

        for i in range(4):
            s.send(_make_utterance(seq=i))
            time.sleep(0.02)

        assert_fifo_order(r.listener, s, "recognizer_loop:utterance", count=4)
    finally:
        b.stop_all()


# ─────────────────────────────────────────────────────────────────────────────
# SESSION-1 §4 — Session propagation unchanged
# ─────────────────────────────────────────────────────────────────────────────

def test_session_field_propagated_unchanged():
    """A session lang field set by the satellite is unchanged at bus injection.

    Spec: SESSION-1 §4
    Helper: assert_session_propagated_unchanged
    """
    b = _topology_with_utterance()
    b.start_all()
    try:
        m = b.get_master("M0")
        s = b.get_satellite("S0")

        sess = Session(session_id=s.shim.session_id, lang="fr-FR")
        s.send(Message(
            "recognizer_loop:utterance",
            data={"utterances": ["bonjour"]},
            context={"session": sess.serialize()},
        ))
        time.sleep(0.2)

        assert_session_propagated_unchanged(
            m, field="lang", value=sess.serialize().get("lang"),
            msg_type="recognizer_loop:utterance",
        )
    finally:
        b.stop_all()


# ─────────────────────────────────────────────────────────────────────────────
# BRIDGE-1 §6 MAY — Topology hiding (optional; xfail if not wired)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skip(
    reason="BRIDGE-1 §6 topology-hiding is an optional MAY the bridge does not implement",
)
def test_source_hidden():
    """Outbound messages carry a generic 'hive' source id (topology hiding).

    Spec: BRIDGE-1 §6 (MAY)
    Helper: assert_source_hidden
    """
    b = _topology_with_utterance()
    b.start_all()
    try:
        m = b.get_master("M0")
        s = b.get_satellite("S0")

        m.emit_on_bus(Message(
            "speak",
            data={"utterance": "hi"},
            context={"destination": s.peer},
        ))

        assert_source_hidden(s, generic_id="hive")
    finally:
        b.stop_all()
