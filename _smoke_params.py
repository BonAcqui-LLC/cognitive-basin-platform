import sys
sys.path.insert(0, '02_REFERENCE_IMPLEMENTATION')
from natural_math_v5 import default_params, NaturalMathValidationError
from natural_math_v5.parameters import validate_params

p = default_params()
validate_params(p)
print('OK defaults')

# missing param
bad = {k: v for k, v in p.items() if k != 'tau'}
try:
    validate_params(bad)
    print('FAIL missing')
except NaturalMathValidationError:
    print('OK missing param')

# extra param
bad = dict(p); bad['bogus'] = 123
try:
    validate_params(bad)
    print('FAIL extra')
except NaturalMathValidationError:
    print('OK extra param')

# tau <= 0
bad = dict(p); bad['tau'] = 0
try:
    validate_params(bad)
    print('FAIL tau')
except NaturalMathValidationError:
    print('OK tau <= 0')

# r_sq <= iota_sq
bad = dict(p); bad['r_sq'] = 1; bad['iota_sq'] = 2
try:
    validate_params(bad)
    print('FAIL rsq')
except NaturalMathValidationError:
    print('OK r_sq <= iota_sq')

# E0 <= tau
bad = dict(p); bad['E0'] = 1000; bad['tau'] = 5000
try:
    validate_params(bad)
    print('FAIL E0')
except NaturalMathValidationError:
    print('OK E0 <= tau')

# cluster ordering
bad = dict(p); bad['critical_energy'] = 500; bad['low_energy_cutoff'] = 499
try:
    validate_params(bad)
    print('FAIL cluster')
except NaturalMathValidationError:
    print('OK cluster ordering')

# non-int
bad = dict(p); bad['tau'] = '5000'
try:
    validate_params(bad)
    print('FAIL type')
except NaturalMathValidationError:
    print('OK non-int')

# repair bool
bad = dict(p); bad['repair_ignores_distance'] = 1
try:
    validate_params(bad)
    print('FAIL bool')
except NaturalMathValidationError:
    print('OK repair bool')

print('ALL PARAM TESTS PASSED')
