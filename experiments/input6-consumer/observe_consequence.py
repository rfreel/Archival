from __future__ import annotations

import json

from consumer import canonicalize_external_keys


inputs = ["KELVIN", " kelvin ", "Straße", "STRASSE", "INV①"]
outputs = canonicalize_external_keys(inputs)
expected = ["kelvin", "strasse", "inv1"]
if outputs != expected:
    raise SystemExit(f"unexpected consumer output: {outputs!r}")

print(
    json.dumps(
        {
            "metric": "novel_external_keys_canonicalized",
            "input_count": len(inputs),
            "unique_output_count": len(outputs),
            "outputs": outputs,
            "status": "PASS",
        },
        sort_keys=True,
    )
)
