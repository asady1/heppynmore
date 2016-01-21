#!/bin/sh

#QCDHT 700
for i in `seq 0 20 120`
do
python generalTreeAnalyzer_v9_pt.py --pathIn=/eos/uscms/store/group/lpchbb/HeppyNtuples/V14/QCD_HT700to1000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V14_QCD_HT700to1000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8__RunIISpring15MiniAODv2-74X_mcRun2_asymptotic_v2-v1/151025_083726/0000/ --outName=QCD_HT700_v9_pt --min=$i --max=$((i+20)) --file=TxtFiles/QCD_HT_700to1000.txt &
done

python generalTreeAnalyzer_v9_pt.py --pathIn=/eos/uscms/store/group/lpchbb/HeppyNtuples/V14/QCD_HT700to1000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V14_QCD_HT700to1000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8__RunIISpring15MiniAODv2-74X_mcRun2_asymptotic_v2-v1/151025_083726/0000/ --outName=QCD_HT700_v9_pt --min=140 --max=158 --file=TxtFiles/QCD_HT_700to1000.txt &
#201 or 198
