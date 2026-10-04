"""Exact evidence shape only; fixture text is not factual approval."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import provision_goyang as provision


class ExactCrossDistrictTests(unittest.TestCase):
    def setUp(self):
        self.source='https://www.anyang.go.kr/main/downloadBbsFile.do?atchmnflNo=810157'
        self.coverage={'siteKey':'anyang-flower-v2','officialSourceUrls':[self.source]}
        self.alias={'aliasKey':'안양시/동안구/행정동/비산1동','districtKey':'dongan'}
        self.unit={'unitKey':'안양시/만안구/법정동/안양동','districtKeys':['manan']}
        self.relation={'scope':'partial','crossDistrictEvidence':{'legalDistrictKey':'manan',
            'administrativeDistrictKey':'dongan','sourceUrl':self.source,
            'sourceLocator':'조례 제3853호 별표2','claim':'Synthetic evidence shape only'}}
    def check(self):
        return provision.exact_cross_district_evidence(self.coverage,self.alias,self.unit,self.relation)
    def test_exact_pair_only(self):
        self.assertTrue(self.check())
        for document,key in [(self.coverage,'siteKey'),(self.alias,'aliasKey'),(self.alias,'districtKey'),(self.unit,'unitKey')]:
            original=document[key];document[key]='other'
            self.assertFalse(self.check());document[key]=original
    def test_missing_wrong_or_extra_evidence_is_not_an_exception(self):
        original=copy.deepcopy(self.relation['crossDistrictEvidence'])
        for key in original:
            self.relation['crossDistrictEvidence']={k:v for k,v in original.items() if k!=key}
            self.assertFalse(self.check())
        self.relation['crossDistrictEvidence']={**original,'extra':'unknown'};self.assertFalse(self.check())
        self.relation['crossDistrictEvidence']={**original,'sourceUrl':'https://example.com/'};self.assertFalse(self.check())
    def test_not_a_whole_district_or_source_free_override(self):
        self.relation['scope']='whole';self.assertFalse(self.check())
        self.relation['scope']='partial';self.coverage['officialSourceUrls']=[];self.assertFalse(self.check())
    def test_only_anyang_gets_new_pin(self):
        profiles=provision.INITIAL_SOURCE_PROFILES
        self.assertEqual(profiles['namyangju-flower-v2']['sourceRevision'],'cbf988f15527d951f72fa68391f6a03f84e29476')
        self.assertEqual(profiles['pyeongtaek-flower-v2'],profiles['namyangju-flower-v2'])
        self.assertEqual(profiles['anyang-flower-v2']['sourceRevision'],'d7f7f15348c78d601356dcff2aaca2b3e426e216')


if __name__=='__main__':unittest.main()
