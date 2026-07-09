# Evolution 2.0 Prize Submission

## Substrate Description
A system of ordinary differential equations (ODEs) modeling chemical reaction networks whose fixed points correspond to stored patterns. The ODEs implement a Hopfield network with Hill-type activation functions.

## Encoder-Message-Decoder Architecture
- **Encoder:** Chemical concentrations evolve under ODE dynamics to a fixed attractor.
- **Message:** Construction A+ readout (PCA + ternary quantization) produces discrete glyphs.
- **Decoder:** Glyph maps to attractor basin for pattern retrieval.

## Vocabulary Statistics
- Vocabulary size: 54
- Shannon entropy H(V): 5.755 bits
- Collisions: 0

## Token Replay Test
- Mean replay hit rate: 1.000
- Null control hit rate: 0.000
- Random control hit rate: 0.000
- Separation score Λ: 1.000

## Conclusion
Status: **PASS** — Prize thresholds satisfied.
