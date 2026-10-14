"""Synthetic/source-generic fixtures only. No target page copy."""
import unittest
from normalization import normalize, lexical_candidates, front_placement, opening_windows, calculate, VALUES
class Mechanics(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize('  A\tB\n&amp; C  '), 'A B & C')
        self.assertEqual(normalize('\u1100\u1161'), '가')
    def test_spacing_and_spans(self):
        self.assertEqual(lexical_candidates('도시 꽃 배달 | 조건', '도시 꽃배달'), [[0,7]])
    def test_exact_short_title_front(self):
        self.assertTrue(front_placement('도시 서비스',[0,6])['front_test'])
    def test_after_separator(self):
        self.assertFalse(front_placement('안내 | 도시 서비스',[5,11])['front_test'])
    def test_raw_newline(self):
        self.assertFalse(front_placement('안내\n도시 서비스',[3,9])['front_test'])
    def test_windows(self):
        self.assertEqual(len(opening_windows('가'*200)['first_120']),120)
        self.assertEqual(len(opening_windows('가'*200)['first_180']),180)
    def test_arithmetic_and_cap(self):
        rows={k:max(v) for k,v in VALUES.items()}
        self.assertEqual(calculate(rows)['raw_score'],100)
        self.assertEqual(calculate(rows,['G1'])['effective_score'],89)
        self.assertEqual(calculate(rows,['G1','G5'])['effective_score'],89)
    def test_unknown(self):
        rows={k:max(v) for k,v in VALUES.items()}; rows['A1']=None
        out=calculate(rows)
        self.assertIsNone(out['raw_score'])
        self.assertEqual(out['possible_raw_range'],[85,100])
        self.assertEqual(out['verdict'],'A04_UNVERIFIED')
    def test_discrete_values(self):
        rows={k:max(v) for k,v in VALUES.items()}; rows['A1']=14
        with self.assertRaises(ValueError): calculate(rows)
if __name__=='__main__': unittest.main(verbosity=2)
