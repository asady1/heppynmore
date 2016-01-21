#!/bin/sh

#QCDHT 500
for i in `seq 0 20 180`
do
python generalTreeAnalyzer_v9_pt.py --pathIn=/eos/uscms/store/group/lpchbb/HeppyNtuples/V14/QCD_HT500to700_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V14_QCD_HT500to700_TuneCUETP8M1_13TeV-madgraphMLM-pythia8__RunIISpring15MiniAODv2-74X_mcRun2_asymptotic_v2-v1/151024_181957/0000/ --outName=QCD_HT500_v9_pt --min=$i --max=$((i+20)) --file=TxtFiles/QCD_HT_500to700.txt &
done

python generalTreeAnalyzer_v9_pt.py --pathIn=/eos/uscms/store/group/lpchbb/HeppyNtuples/V14/QCD_HT500to700_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V14_QCD_HT500to700_TuneCUETP8M1_13TeV-madgraphMLM-pythia8__RunIISpring15MiniAODv2-74X_mcRun2_asymptotic_v2-v1/151024_181957/0000/ --outName=QCD_HT500_v9_pt --min=200 --max=214 --file=TxtFiles/QCD_HT_500to700.txt &
#253 or 250?

