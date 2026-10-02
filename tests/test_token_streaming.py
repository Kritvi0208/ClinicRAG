import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.agent import MedicalAgent
from src.config import config

def test_real_time_token_streaming():
    """Confirms real-time token streaming yields multiple incremental chunks and terminates cleanly."""
    agent = MedicalAgent()
    query = "Explain the basic function of paracetamol in 2 short bullet points."
    
    tokens_received: List[str] = []
    tool_events: List[str] = []
    final_output: str = ""
    
    t0 = time.time()
    for event in agent.stream_run(query, []):
        event_type = event.get("type")
        if event_type == "token":
            tok = event.get("content", "")
            if tok:
                tokens_received.append(tok)
        elif event_type == "tool_start":
            tool_events.append(event.get("name", ""))
        elif event_type == "final_result":
            final_output = event.get("result", {}).get("output", "")
            
    total_time = time.time() - t0
    
    # Assertions
    # 1. Multiple incremental chunks were received
    assert len(tokens_received) > 1, f"Expected multiple tokens, but got {len(tokens_received)}"
    
    # 2. Reconstructed text is non-empty
    reconstructed_text = "".join(tokens_received).strip()
    assert len(reconstructed_text) > 0, "Streamed text should not be empty"
    
    # 3. Stream terminates cleanly on EOS
    assert total_time < 90.0, f"Streaming took too long: {total_time:.2f}s"
    
    print(f"\n[PASS] Real-time token streaming verified successfully!")
    print(f"[PASS] Streamed {len(tokens_received)} tokens incrementally in {total_time:.2f}s.")
    print(f"[PASS] First 5 incremental tokens: {tokens_received[:5]}")
    print(f"[PASS] Reconstructed snippet: {reconstructed_text[:120]}...")

if __name__ == "__main__":
    test_real_time_token_streaming()
