#!/bin/sh

#QCDHT 1000
for i in `seq 0 20 40`
do
python generalTreeAnalyzer_v9_pt.py --pathIn=/eos/uscms/store/group/lpchbb/HeppyNtuples/V14/QCD_HT1000to1500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V14_QCD_HT1000to1500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8__RunIISpring15MiniAODv2-74X_mcRun2_asymptotic_v2-v1/151025_083753/0000/ --outName=QCD_HT1000_v9_pt --min=$i --max=$((i+20)) --file=TxtFiles/QCD_HT_1000to1500.txt &
done

#QCDHT 1500
for i in `seq 0 20 20`
do
python generalTreeAnalyzer_v9_pt.py --pathIn=/eos/uscms/store/group/lpchbb/HeppyNtuples/V14/QCD_HT1500to2000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V14_QCD_HT1500to2000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8__RunIISpring15MiniAODv2-74X_mcRun2_asymptotic_v2-v1/151025_093151/0000/ --outName=QCD_HT1500_v9_pt --min=$i --max=$((i+20)) --file=TxtFiles/QCD_HT_1500to2000.txt &
done
#QCDHT 2000
python generalTreeAnalyzer_v9_pt.py --pathIn=/eos/uscms/store/group/lpchbb/HeppyNtuples/V14/QCD_HT2000toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V14_QCD_HT2000toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8__RunIISpring15MiniAODv2-74X_mcRun2_asymptotic_v2-v1/151024_184123/0000/ --outName=QCD_HT2000_v9_pt --min=0 --max=11 --file=TxtFiles/QCD_HT_2000toInf.txt  &

python generalTreeAnalyzer_v9_pt.py --pathIn=/eos/uscms/store/group/lpchbb/HeppyNtuples/V14/QCD_HT2000toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V14_QCD_HT2000toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8__RunIISpring15MiniAODv2-74X_mcRun2_asymptotic_v2-v1/151024_184123/0000/ --outName=QCD_HT2000_v9_pt --min=11 --max=22 --file=TxtFiles/QCD_HT_2000toInf.txt  &
#35 or 34

