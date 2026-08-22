# Perfect Cuboid — Extension-Field Motive Iteration

## Exact scope

The simulator exhaustively evaluated all `(b,c)` over 32 finite fields `F_(p^n)`, with maximum field size 2,401. Arithmetic used explicit polynomial-basis finite fields.

## Result

- all 16 character-sum formulas: **True**
- Euler count formula: **True**
- full count formula: **True**
- Frobenius recurrences for E4 and E8: **True**
- symmetric-square fingerprints: **True**

| p  | n | q    | chi(-1) | chi(2) | t4  | t8  | Euler  | Full   |
| -- | - | ---- | ------- | ------ | --- | --- | ------ | ------ |
| 3  | 1 | 3    | -1      | -1     | 0   | 2   | 1      | 1      |
| 3  | 2 | 9    | 1       | 1      | -6  | -2  | 25     | 25     |
| 3  | 3 | 27   | -1      | -1     | 0   | -10 | 73     | 49     |
| 3  | 4 | 81   | 1       | 1      | 18  | -14 | 913    | 577    |
| 3  | 5 | 243  | -1      | -1     | 0   | 2   | 7321   | 3601   |
| 3  | 6 | 729  | 1       | 1      | -54 | 46  | 67465  | 34969  |
| 5  | 1 | 5    | 1       | -1     | -2  | 0   | 5      | 5      |
| 5  | 2 | 25   | 1       | 1      | -6  | -10 | 121    | 97     |
| 5  | 3 | 125  | 1       | -1     | 22  | 0   | 1997   | 1157   |
| 5  | 4 | 625  | 1       | 1      | -14 | 50  | 49777  | 25633  |
| 7  | 1 | 7    | -1      | 1      | 0   | 0   | 9      | 5      |
| 7  | 2 | 49   | 1       | 1      | -14 | -14 | 385    | 289    |
| 7  | 3 | 343  | -1      | 1      | 0   | 0   | 14793  | 7397   |
| 7  | 4 | 2401 | 1       | 1      | 98  | 98  | 724129 | 366529 |
| 11 | 1 | 11   | -1      | -1     | 0   | 6   | 9      | 9      |
| 11 | 2 | 121  | 1       | 1      | -22 | 14  | 1993   | 1177   |
| 11 | 3 | 1331 | -1      | -1     | 0   | 18  | 221073 | 110265 |
| 13 | 1 | 13   | 1       | -1     | 6   | 0   | 21     | 21     |
| 13 | 2 | 169  | 1       | 1      | 10  | -26 | 3817   | 2113   |
| 13 | 3 | 2197 | 1       | -1     | -18 | 0   | 604461 | 303669 |
| 17 | 1 | 17   | 1       | 1      | 2   | -6  | 57     | 41     |
| 17 | 2 | 289  | 1       | 1      | -30 | 2   | 10753  | 5665   |
| 19 | 1 | 19   | -1      | -1     | 0   | 2   | 41     | 17     |
| 19 | 2 | 361  | 1       | 1      | -38 | -34 | 16825  | 9049   |
| 23 | 1 | 23   | -1      | 1      | 0   | 0   | 73     | 37     |
| 23 | 2 | 529  | 1       | 1      | -46 | -46 | 35809  | 18913  |
| 29 | 1 | 29   | 1       | -1     | -10 | 0   | 125    | 101    |
| 29 | 2 | 841  | 1       | 1      | 42  | -58 | 89641  | 46081  |
| 31 | 1 | 31   | -1      | 1      | 0   | 0   | 129    | 65     |
| 31 | 2 | 961  | 1       | 1      | -62 | -62 | 116929 | 60289  |
| 37 | 1 | 37   | 1       | -1     | -2  | 0   | 189    | 117    |
| 37 | 2 | 1369 | 1       | 1      | -70 | -74 | 236377 | 120673 |

## Motive-level fingerprint

For an elliptic curve over `F_q` with trace `t`,

`Tr(Sym^2 H^1)=t^2-q`,

and the local polynomial is

`1-(t^2-q)T+(q*t^2-q^2)T^2-q^3T^3`.

The hard sums reduce to:

- `S7 = chi(-1)(t8^2-q)+(2chi(2)+chi(-1))q+2`
- `S11 = (t4^2-q)+(1-chi(-1))q+2`
- `S13=S14 = (t4^2-q)-chi(-1)q+(1+chi(-1))`
- `S15 = 3(t8^2-q)+(2-2chi(-1)chi(2))q+(2+chi(-1))`

This separates Tate/boundary terms from two CM symmetric-square traces.

## Extension activation

| p  | curve | first active n | trace |
| -- | ----- | -------------- | ----- |
| 3  | t4    | 2              | -6    |
| 5  | t8    | 2              | -10   |
| 7  | t4    | 2              | -14   |
| 7  | t8    | 2              | -14   |
| 11 | t4    | 2              | -22   |
| 13 | t8    | 2              | -26   |
| 19 | t4    | 2              | -38   |
| 23 | t4    | 2              | -46   |
| 23 | t8    | 2              | -46   |
| 29 | t8    | 2              | -58   |
| 31 | t4    | 2              | -62   |
| 31 | t8    | 2              | -62   |
| 37 | t8    | 2              | -74   |

A trace that vanishes over `F_p` can reactivate over `F_(p^2)`. Prime-congruence simplifications therefore do not imply the motive is absent.

## New distinctions

| id  | left                             | right                                       | status                 |
| --- | -------------------------------- | ------------------------------------------- | ---------------------- |
| D74 | Prime-field point-count identity | Identity over F_(p^n)                       | extension-tested       |
| D75 | Elliptic trace t                 | Symmetric-square trace t^2-q                | structural split       |
| D76 | Formula by p mod 8               | Formula by chi(-1), chi(2)                  | finite-field invariant |
| D77 | CM trace vanishes over F_p       | Trace activates over an extension           | observed               |
| D78 | Numerical fit across primes      | Frobenius-recurrence-compatible fingerprint | stronger               |
| D79 | Tate/boundary terms              | Transcendental CM terms                     | separated              |
| D80 | j=1728 contribution              | j=8000 contribution                         | independent            |
| D81 | Affine character sum             | Compactified trace plus boundary correction | different objects      |
| D82 | Vary p                           | Vary extension degree n at fixed p          | new axis               |
| D83 | Count equality                   | All 16 character-sum equalities             | stronger               |
| D84 | Extension-field identity         | Explicit correspondence/motivic proof       | still open             |

## Limit

Extension-field agreement is much stronger than fitting unrelated prime counts, but it is not yet an explicit algebraic correspondence or proof of motive decomposition.
