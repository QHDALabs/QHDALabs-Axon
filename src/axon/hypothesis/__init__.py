"""
Stage 4 — hypothesis.

Discoveries are the OUTPUT of verification, never an input to it. A hypothesis
module that runs before verification is a bug. Structurally, this stage accepts
only verified results (``VerificationResult``) — it cannot be fed raw candidates.
"""
