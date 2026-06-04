# GMAT Validation Drivers

This directory contains repo-side drivers executed inside the GMAT validation image. They are internal validation plumbing, not public SDK examples.

Drivers use JSON over stdin/stdout:

- stdin is one normalized tool-neutral JSON payload;
- stdout is one normalized JSON result;
- stderr and nonzero exits are reserved for loud tool failures;
- drivers do not import ASTROX, pytest, or project dependencies;
- drivers do not own comparison tolerances.

Host-side validation scripts own public SDK input construction, live ASTROX calls, normalized driver payloads, residual computation, and failure messages. GMAT drivers only translate normalized comparison cases into GMAT execution and emit sampled Cartesian states in meters and meters per second.
