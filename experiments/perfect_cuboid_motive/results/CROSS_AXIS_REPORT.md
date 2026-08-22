# Perfect Cuboid — Ramified/Unramified Cross-Axis Iteration

## Exact scope

For matched cardinalities `p^k`, this run compared:

- the reduced field `F_(p^k)`, which changes Frobenius/residue-field degree;
- the nonreduced local ring `Z/p^k Z`, which changes nilpotent/jet thickness.

There were 32 matched cases. At depth one, all field and ring counts agreed: **True**.

## Main result

Beyond depth one, equal cardinality does not imply equal cuboid-local geometry.

- cases with different Euler or full counts: **21**
- cases with different redundancy status: **7**

| p  | depth | p^depth | field E/F     | ring E/F       | field survival | ring survival | same redundancy |
| -- | ----- | ------- | ------------- | -------------- | -------------- | ------------- | --------------- |
| 3  | 1     | 3       | 1/1           | 1/1            | 1.000000       | 1.000000      | 1               |
| 3  | 2     | 9       | 25/25         | 9/9            | 1.000000       | 1.000000      | 1               |
| 3  | 3     | 27      | 73/49         | 45/45          | 0.671233       | 1.000000      | 0               |
| 3  | 4     | 81      | 913/577       | 405/405        | 0.631982       | 1.000000      | 0               |
| 3  | 5     | 243     | 7321/3601     | 3321/3321      | 0.491873       | 1.000000      | 0               |
| 3  | 6     | 729     | 67465/34969   | 29889/29889    | 0.518328       | 1.000000      | 0               |
| 5  | 1     | 5       | 5/5           | 5/5            | 1.000000       | 1.000000      | 1               |
| 5  | 2     | 25      | 121/97        | 45/45          | 0.801653       | 1.000000      | 0               |
| 5  | 3     | 125     | 1997/1157     | 725/645        | 0.579369       | 0.889655      | 1               |
| 5  | 4     | 625     | 49777/25633   | 12125/8525     | 0.514957       | 0.703093      | 1               |
| 7  | 1     | 7       | 9/5           | 9/5            | 0.555556       | 0.555556      | 1               |
| 7  | 2     | 49      | 385/289       | 441/245        | 0.750649       | 0.555556      | 1               |
| 7  | 3     | 343     | 14793/7397    | 20433/10829    | 0.500034       | 0.529976      | 1               |
| 7  | 4     | 2401    | 724129/366529 | 1001217/530621 | 0.506165       | 0.529976      | 1               |
| 11 | 1     | 11      | 9/9           | 9/9            | 1.000000       | 1.000000      | 1               |
| 11 | 2     | 121     | 1993/1177     | 1089/1089      | 0.590567       | 1.000000      | 0               |
| 11 | 3     | 1331    | 221073/110265 | 124509/124509  | 0.498772       | 1.000000      | 0               |
| 13 | 1     | 13      | 21/21         | 21/21          | 1.000000       | 1.000000      | 1               |
| 13 | 2     | 169     | 3817/2113     | 2925/1677      | 0.553576       | 0.573333      | 1               |
| 13 | 3     | 2197    | 604461/303669 | 478101/257205  | 0.502380       | 0.537972      | 1               |
| 17 | 1     | 17      | 57/41         | 57/41          | 0.719298       | 0.719298      | 1               |
| 17 | 2     | 289     | 10753/5665    | 11929/4041     | 0.526830       | 0.338754      | 1               |
| 19 | 1     | 19      | 41/17         | 41/17          | 0.414634       | 0.414634      | 1               |
| 19 | 2     | 361     | 16825/9049    | 14801/6137     | 0.537831       | 0.414634      | 1               |
| 23 | 1     | 23      | 73/37         | 73/37          | 0.506849       | 0.506849      | 1               |
| 23 | 2     | 529     | 35809/18913   | 38617/19573    | 0.528163       | 0.506849      | 1               |
| 29 | 1     | 29      | 125/101       | 125/101        | 0.808000       | 0.808000      | 1               |
| 29 | 2     | 841     | 89641/46081   | 62901/23229    | 0.514062       | 0.369295      | 1               |
| 31 | 1     | 31      | 129/65        | 129/65         | 0.503876       | 0.503876      | 1               |
| 31 | 2     | 961     | 116929/60289  | 123969/62465   | 0.515603       | 0.503876      | 1               |
| 37 | 1     | 37      | 189/117       | 189/117        | 0.619048       | 0.619048      | 1               |
| 37 | 2     | 1369    | 236377/120673 | 189477/48285   | 0.510511       | 0.254833      | 1               |

## First visible failure on each axis

| p  | first field-extension failure n | first ring-jet failure m |
| -- | ------------------------------- | ------------------------ |
| 3  | 3                               | none                     |
| 5  | 2                               | 3                        |
| 7  | 1                               | 1                        |
| 11 | 2                               | none                     |
| 13 | 2                               | 2                        |
| 17 | 1                               | 1                        |
| 19 | 1                               | 1                        |
| 23 | 1                               | 1                        |
| 29 | 1                               | 1                        |
| 31 | 1                               | 1                        |
| 37 | 1                               | 1                        |

The sharp examples are:

- `p=3`: the fourth equation remains redundant through every tested ramified depth, but fails over `F_(3^3)`;
- `p=5`: it fails over `F_(5^2)` but only at ring depth `5^3`;
- `p=11`: it remains redundant in every tested ramified jet and over `Q_11`, but fails over `F_(11^2)`;
- `p=13`: both axes first fail at depth two, with different counts and singular mechanisms.

## Interpretation

`Q_p`-redundancy and geometric redundancy over the residue closure are different claims.

Ramified depth probes lifting along one residue point and is governed by valuations, Jacobian rank, and singular strata. Unramified degree probes new residue-field points and is governed by Frobenius eigenvalues and the two CM symmetric-square pieces found in the motive iteration.

Thus the local state is genuinely two-dimensional:

`(ramification depth m, residue extension degree n)`.

Neither axis can substitute for the other.

## New distinctions

| id  | left                            | right                                          | status                                      |
| --- | ------------------------------- | ---------------------------------------------- | ------------------------------------------- |
| D85 | Ramified jet depth m            | Unramified residue extension degree n          | orthogonal axes                             |
| D86 | Z/p^mZ with p^m elements        | F_(p^m) with p^m elements                      | same cardinality, different geometry        |
| D87 | Nilpotent thickening            | Reduced finite-field extension                 | different local information                 |
| D88 | Hensel/Greenberg branching      | Frobenius trace recurrence                     | different transition laws                   |
| D89 | Redundant on F_p-points         | Redundant on all geometric points over Fbar_p  | not equivalent                              |
| D90 | Redundant over Q_p              | Redundant over finite residue extensions       | not equivalent                              |
| D91 | Trace zero at degree one        | Motive absent                                  | false implication                           |
| D92 | Singular q3=0 jet failure       | CM motive activation over F_(p^2)              | different mechanisms                        |
| D93 | Failure first visible at p^m    | Failure first visible at F_(p^n)               | separate depths                             |
| D94 | Arithmetic local point over Q_p | Geometric point over algebraic residue closure | different loci                              |
| D95 | Local-ring density              | Finite-field point-count density               | same leading scale, different corrections   |
| D96 | Prime-field coincidence         | Axis-stable identity                           | requires both ramified and unramified tests |

## Verification

- every depth-one ring count equals the corresponding prime-field count;
- every ring count is an exhaustive enumeration;
- every field count was independently verified by the 16-character-sum and motive formulas;
- the comparison is descriptive and does not assert a local or global nonexistence theorem.
