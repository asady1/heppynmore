#!/usr/bin/env python
import os, sys, ROOT, warnings, pickle
from ROOT import TFile
from array import array
from math import sqrt
from copy import copy
#suppres the EvalInstace conversion warning bug
warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='creating converter.*' )
from optparse import OptionParser
from BetterConfigParser import BetterConfigParser
from samplesclass import sample
from mvainfos import mvainfo
from progbar import progbar
from printcolor import printc
from gethistofromtree import getHistoFromTree, orderandadd

#CONFIGURE
argv = sys.argv
parser = OptionParser()
parser.add_option("-P", "--path", dest="path", default="",
                      help="path to samples")
parser.add_option("-V", "--var", dest="variable", default="",
                      help="variable for shape analysis")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
(opts, args) = parser.parse_args(argv)
if opts.config =="":
        opts.config = "config"
print opts.config
config = BetterConfigParser()
config.read(opts.config)
anaTag = config.get("Analysis","tag")


# -------------------- parsing configuration and options: (an ugly spaghetti code section) ----------------------------------------------------------------------
#get locations:
Wdir=config.get('Directories','Wdir')
vhbbpath=config.get('Directories','vhbbpath')
samplesinfo=config.get('Directories','samplesinfo')
#systematics
systematics=config.get('systematics','systematics')
systematics=systematics.split(' ')
weightF=config.get('Weights','weightF')
path=opts.path
var=opts.variable
plot=config.get('Limit',var)
infofile = open(samplesinfo,'r')
info = pickle.load(infofile)
infofile.close()
options = plot.split(',')
if len(options) < 12:
    print "You have to choose option[11]: either Mjj or BDT"
    sys.exit("You have to choose option[11]: either Mjj or BDT")
name=options[1]
title = options[2]
nBinsRB=int(options[3])
nBins= int(config.get('LimitGeneral','BDTbinning'))
xMin=float(options[4])
xMax=float(options[5])
SIG=options[9]
data=options[10]
anType=options[11]
RCut=options[7]
setup=eval(config.get('LimitGeneral','setup'))
ROOToutname = options[6]

if 'HighPtLooseBTag' in ROOToutname:
    pt_region = 'HighPtLooseBTag'
elif 'HighPt' in ROOToutname or 'highPt' in ROOToutname or 'medPt' in ROOToutname:
    pt_region = 'HighPt'
elif 'LowPt' in ROOToutname or 'lowPt' in ROOToutname:
    pt_region = 'LowPt'
else: 
    print "Unknown Pt region"
    sys.exit("Unknown Pt region")

outpath=config.get('Directories','limits')
systematicsnaming=eval(config.get('LimitGeneral','systematicsnaming7TeV'))

TrainFlag = eval(config.get('Analysis','TrainFlag'))



if anaTag =='8TeV':
    systematicsnaming=eval(config.get('LimitGeneral','systematicsnaming8TeV'))
elif not anaTag =='7TeV':
    print "What is your Analysis Tag in config? (anaTag)"
    sys.exit("What is your Analysis Tag in config? (anaTag)")
scaling=eval(config.get('LimitGeneral','scaling'))
sys_factor_dict = eval(config.get('LimitGeneral','sys_factor'))

if TrainFlag:
    MC_rescale_factor=2.
    print 'I RESCALE BY 2.0'
else: MC_rescale_factor = 1.

rescaleSqrtN=eval(config.get('LimitGeneral','rescaleSqrtN'))
if 'RTight' in RCut:
    Datacardbin=options[10]
elif 'RMed' in RCut:
    Datacardbin=options[10]
else:
    Datacardbin=options[10]
blind=eval(config.get('LimitGeneral','blind'))
BKGlist = eval(config.get('LimitGeneral','BKG'))
#Groups for adding samples together
Group = eval(config.get('LimitGeneral','Group'))
#naming for DC
Dict= eval(config.get('LimitGeneral','Dict'))
weightF_sys = eval(config.get('LimitGeneral','weightF_sys'))
binstat = eval(config.get('LimitGeneral','binstat'))
addSample_sys = None if not config.has_option('LimitGeneral','addSample_sys') else eval(config.get('LimitGeneral','addSample_sys'))
bdt = False
mjj = False
#print str(anType)
#print len(options)
if str(anType) == 'BDT':
    bdt = True
    systematics = eval(config.get('LimitGeneral','sys_BDT'))
elif str(anType) == 'Mjj':
    mjj = True
    systematics = eval(config.get('LimitGeneral','sys_Mjj'))
sys_cut_suffix=eval(config.get('LimitGeneral','sys_cut_suffix'))
sys_affecting = eval(config.get('LimitGeneral','sys_affecting'))
rebin_active=eval(config.get('LimitGeneral','rebin_active'))

signal_inject=config.get('LimitGeneral','signal_inject')


outfile = ROOT.TFile(outpath+'vhbb_TH_'+ROOToutname+'.root', 'RECREATE')
outfile.mkdir(Datacardbin,Datacardbin)
outfile.cd(Datacardbin)

class Rebinner:
    def __init__(self,nBins,lowedgearray,active=True):
        self.lowedgearray=lowedgearray
        self.nBins=nBins
        self.active=active
    def rebin(self, histo):
        if not self.active: return histo
        histo.Rebin(self.nBins,'hnew',self.lowedgearray)
        binhisto=ROOT.gDirectory.Get('hnew')
        newhisto=ROOT.TH1F('new','new',self.nBins,self.lowedgearray[0],self.lowedgearray[-1])
        newhisto.Sumw2()
        for bin in range(0,self.nBins+1):
            newhisto.SetBinContent(bin,binhisto.GetBinContent(bin))
            newhisto.SetBinError(bin,binhisto.GetBinError(bin))
            newhisto.SetName(binhisto.GetName())
            newhisto.SetTitle(binhisto.GetTitle())
        return newhisto



# -------------------- generate the Workspace with all Histograms: ----------------------------------------------------------------------

WS = ROOT.RooWorkspace('%s'%Datacardbin,'%s'%Datacardbin) #Zee
print 'WS initialized'
disc= ROOT.RooRealVar(name,name,xMin,xMax)
obs = ROOT.RooArgList(disc)
ROOT.gROOT.SetStyle("Plain")
datas = []
datatyps =[]
histos = []
typs = []
hNames = []
aNames = []
statUps=[]
statDowns=[]
if blind: 
    printc('red','', 'I AM BLINDED!')  



#---- get the BKG for the rebinning calculation----
counterRB=0
injection = False

for job in info:
    if eval(job.active):
        if job.subsamples:
            for subsample in range(0,len(job.subnames)):
                if job.subnames[subsample] in BKGlist:
                    hTemp, typ = getHistoFromTree(job,path,config,options,MC_rescale_factor,subsample)
                    if counterRB == 0:
                        hDummyRB = copy(hTemp)
                    else:
                        hDummyRB.Add(hTemp)
                    counterRB += 1
                    
        else:
            if job.name in BKGlist:
                hTemp, typ = getHistoFromTree(job,path,config,options,MC_rescale_factor)
                if counterRB == 0:
                    hDummyRB = copy(hTemp)
                else:
                    hDummyRB.Add(hTemp)
                counterRB += 1


            elif job.name == signal_inject:
                inject_SIG, _ = getHistoFromTree(job,path,config,options,MC_rescale_factor)
                injection = True

ErrorR=0
ErrorL=0
TotR=0
TotL=0
binR=nBinsRB
binL=1
rel=1.0
#---- from right
while rel > 0.35:
    TotR+=hDummyRB.GetBinContent(binR)
    ErrorR=sqrt(ErrorR**2+hDummyRB.GetBinError(binR)**2)
    binR-=1
    if not TotR == 0 and not ErrorR == 0:
        rel=ErrorR/TotR
        #print rel
print 'upper bin is %s'%binR

#---- from left
rel=1.0
while rel > 0.35:
    TotL+=hDummyRB.GetBinContent(binL)
    ErrorL=sqrt(ErrorL**2+hDummyRB.GetBinError(binL)**2)
    binL+=1
    if not TotL == 0 and not ErrorL == 0:
        rel=ErrorL/TotL
        #print rel
print 'lower bin is %s'%binL

inbetween=binR-binL
stepsize=int(inbetween)/(int(nBins)-2)
modulo = int(inbetween)%(int(nBins)-2)

print'stepsize %s'% stepsize
print 'modulo %s'%modulo

binlist=[binL]
for i in range(0,int(nBins)-3):
    binlist.append(binlist[-1]+stepsize)
binlist[-1]+=modulo
binlist.append(binR)
binlist.append(nBinsRB+1)

print binlist
myBinning=Rebinner(int(nBins),array('d',[-1.0]+[hDummyRB.GetBinLowEdge(i) for i in binlist]),rebin_active)
#--------------------------------------------------


if injection: hDummyRB.Add(inject_SIG)
hDummy=myBinning.rebin(hDummyRB)


if weightF_sys:
    weightF_sys_UP=config.get('Weights','weightF_sys_UP')
    weightF_sys_DOWN=config.get('Weights','weightF_sys_DOWN')
    weightF_sys_Ups = []
    weightF_sys_Downs = []
if addSample_sys:
    sTyps = []
    addSample_sys_histos = []
    aSample_sys_Ups = []
    aSample_sys_Downs = []

for job in info:
    if eval(job.active):
        if job.subsamples:
            for subsample in range(0,len(job.subnames)):
                if job.subnames[subsample] in BKGlist:
                    print 'getting %s'%job.subnames[subsample]
                    hTemp, typ = getHistoFromTree(job,path,config,options,MC_rescale_factor,subsample)
                    print hTemp.Integral()
                    histos.append(myBinning.rebin(hTemp))
                    typs.append(Group[job.subnames[subsample]])
                    hNames.append(job.subnames[subsample])                        
                    if weightF_sys:
                        hTempWU, _ = getHistoFromTree(job,path,config,options,MC_rescale_factor,subsample,'weightF_sys_UP')
                        weightF_sys_Ups.append(myBinning.rebin(hTempWU))
                        hTempWD, _ = getHistoFromTree(job,path,config,options,MC_rescale_factor,subsample,'weightF_sys_DOWN')
                        weightF_sys_Downs.append(myBinning.rebin(hTempWD))

                elif job.subnames[subsample] == SIG:
                    hNames.append(job.subnames[subsample])
                    print 'getting %s'%job.subnames[subsample]                        
                    hTemp, typ = getHistoFromTree(job,path,config,options,MC_rescale_factor,subsample)
                    print hTemp.Integral()
                    histos.append(myBinning.rebin(hTemp))
                    typs.append(Group[job.subnames[subsample]])
                    if weightF_sys:
                        hTempWU, _ = getHistoFromTree(job,path,config,options,MC_rescale_factor,subsample,'weightF_sys_UP')
                        weightF_sys_Ups.append(myBinning.rebin(hTempWU))
                        hTempWD, _ = getHistoFromTree(job,path,config,options,MC_rescale_factor,subsample,'weightF_sys_DOWN')
                        weightF_sys_Downs.append(myBinning.rebin(hTempWD))
                if addSample_sys and job.subnames[subsample] in addSample_sys.values():
                    aNames.append(job.subnames[subsample])
                    hTempS, s_ = getHistoFromTree(job,path,config,options,MC_rescale_factor,subsample)
                    addSample_sys_histos.append(myBinning.rebin(hTempS))
    
        else:
            if job.name in BKGlist:
                #print job.getpath()
                print 'getting %s'%job.name
                hTemp, typ = getHistoFromTree(job,path,config,options,MC_rescale_factor)
                histos.append(myBinning.rebin(hTemp))
                print hTemp.Integral()
                typs.append(Group[job.name])                        
                hNames.append(job.name)
                if weightF_sys:
                    hTempWU, _ = getHistoFromTree(job,path,config,options,MC_rescale_factor,-1,'weightF_sys_UP')
                    weightF_sys_Ups.append(myBinning.rebin(hTempWU))
                    hTempWD, _ = getHistoFromTree(job,path,config,options,MC_rescale_factor,-1,'weightF_sys_DOWN')
                    weightF_sys_Downs.append(myBinning.rebin(hTempWD))

            elif job.name == SIG:
                print 'getting %s'%job.name
                hTemp, typ = getHistoFromTree(job,path,config,options,MC_rescale_factor)
                histos.append(myBinning.rebin(hTemp))
                print hTemp.Integral()
                typs.append(Group[job.name])                                        
                hNames.append(job.name)                        
                if weightF_sys:
                    hTempWU, _ = getHistoFromTree(job,path,config,options,MC_rescale_factor,-1,'weightF_sys_UP')
                    weightF_sys_Ups.append(myBinning.rebin(hTempWU))
                    hTempWD, _ = getHistoFromTree(job,path,config,options,MC_rescale_factor,-1,'weightF_sys_DOWN')
                    weightF_sys_Downs.append(myBinning.rebin(hTempWD))

            elif job.name in data:
                #print 'DATA'
                print 'getting %s'%job.name
                hTemp, typ = getHistoFromTree(job,path,config,options)
                datas.append(myBinning.rebin(hTemp))
                print hTemp.Integral()
                datatyps.append(typ)
            
            if addSample_sys and job.name in addSample_sys.values():
                aNames.append(job.name)
                hTempS, s_ = getHistoFromTree(job,path,config,options,MC_rescale_factor)
                addSample_sys_histos.append(myBinning.rebin(hTempS))

MC_integral=0
MC_entries=0
for histo in histos:
    MC_integral+=histo.Integral()
    print 'histo integral %s'%histo.Integral()
printc('green','', 'MC integral = %s'%MC_integral)

def getAlternativeShapes(histos,altHistos,hNames,aNames,addSample_sys):
    theHistosUp = []
    theHistosDown = []
    for histo in histos:
        theHistosUp.append(histo.Clone())
        theHistosDown.append(histo.Clone())
    for name in addSample_sys.keys():
        print name
    hVar = altHistos[aNames.index(addSample_sys[name])].Clone()
    hNom = histos[hNames.index(name)].Clone()
    hAlt = hNom.Clone()
    hNom.Add(hVar,-1.)
    hAlt.Add(hNom)
    for bin in range(0,nBins):
        if hAlt.GetBinContent(bin) < 0.: hAlt.SetBinContent(bin,0.)
    theHistosUp[hNames.index(name)] = hVar.Clone()
    theHistosDown[hNames.index(name)] = hAlt.Clone()
    return theHistosUp, theHistosDown

#order and add together
typs2=copy(typs)
typs3=copy(typs)
typs4=copy(typs)
typs5=copy(typs)
if addSample_sys:
    aSampleUp, aSampleDown = getAlternativeShapes(histos,addSample_sys_histos,hNames,aNames,addSample_sys)
histos, typs = orderandadd(histos,typs,setup)
if weightF_sys:
    weightF_sys_Ups,_=orderandadd(weightF_sys_Ups,typs2,setup)
    weightF_sys_Downs,_=orderandadd(weightF_sys_Downs,typs3,setup)

if addSample_sys:
    aSampleUp,aNames=orderandadd(aSampleUp,typs4,setup)
    aSampleDown,aNames=orderandadd(aSampleDown,typs5,setup)

for i in range(0,len(histos)):
    newname=Dict[typs[i]]
    histos[i].SetName(newname)
    #histos[i].SetDirectory(outfile)
    outfile.cd()
    outfile.cd(Datacardbin)
    histos[i].Write()
    errorsum=0
    total=0
    for j in range(histos[i].GetNbinsX()+1):
        errorsum=errorsum+(histos[i].GetBinError(j))**2
    errorsum=sqrt(errorsum)
    total=histos[i].Integral()

    if binstat: #treating statistics in single bins
        for bin in range(0,nBins):
            statUps.append(histos[i].Clone())
            statDowns.append(histos[i].Clone())
            statUps[i*nBins+bin].SetName('%sCMS_vhbb_stats_%s_%s_%sUp'%(newname,newname,bin,options[10]))
            statDowns[i*nBins+bin].SetName('%sCMS_vhbb_stats_%s_%s_%sDown'%(newname,newname,bin,options[10]))
            #shift up and down with statistical error
            if rescaleSqrtN:
                statUps[i*nBins+bin].SetBinContent(bin,statUps[i*nBins+bin].GetBinContent(bin)+statUps[i*nBins+bin].GetBinError(bin)/total*errorsum)
                statDowns[i*nBins+bin].SetBinContent(bin,statDowns[i*nBins+bin].GetBinContent(bin)-statDowns[i*nBins+bin].GetBinError(bin)/total*errorsum)
            else:
                statUps[i*nBins+bin].SetBinContent(bin,statUps[i*nBins+bin].GetBinContent(bin)+statUps[i*nBins+bin].GetBinError(bin))
                statDowns[i*nBins+bin].SetBinContent(bin,statDowns[i*nBins+bin].GetBinContent(bin)-statDowns[i*nBins+bin].GetBinError(bin))
            statUps[i*nBins+bin].Write()
            statDowns[i*nBins+bin].Write()
            histPdf = ROOT.RooDataHist(newname,newname,obs,histos[i])
            #UP stats of MCs
            RooStatsUp = ROOT.RooDataHist('%sCMS_vhbb_stats_%s_%s_%sUp'%(newname,newname,bin,options[10]),'%sCMS_vhbb_stats_%s_%s_%sUp'%(newname,newname,bin,options[10]),obs, statUps[i*nBins+bin])
            #DOWN stats of MCs
            RooStatsDown = ROOT.RooDataHist('%sCMS_vhbb_stats_%s_%s_%sDown'%(newname,newname,bin,options[10]),'%sCMS_vhbb_stats_%s_%s_%sDown'%(newname,newname,bin,options[10]),obs, statDowns[i*nBins+bin])
            getattr(WS,'import')(histPdf)
            getattr(WS,'import')(RooStatsUp)
            getattr(WS,'import')(RooStatsDown)

    else:
        statUps.append(histos[i].Clone())
        statDowns.append(histos[i].Clone())
        statUps[i].SetName('%sCMS_vhbb_stats_%s_%sUp'%(newname,newname,options[10]))
        statDowns[i].SetName('%sCMS_vhbb_stats_%s_%sDown'%(newname,newname,options[10]))
        #shift up and down with statistical error
        for j in range(histos[i].GetNbinsX()+1):
            if rescaleSqrtN:
                statUps[i].SetBinContent(j,statUps[i].GetBinContent(j)+statUps[i].GetBinError(j)/total*errorsum)
                statDowns[i].SetBinContent(j,statDowns[i].GetBinContent(j)-statDowns[i].GetBinError(j)/total*errorsum)
            else:
                statUps[i].SetBinContent(j,statUps[i].GetBinContent(j)+statUps[i].GetBinError(j))
                statDowns[i].SetBinContent(j,statDowns[i].GetBinContent(j)-statDowns[i].GetBinError(j))
            #if statDowns[i].GetBinError(j)<0.: statDowns[i].SetBinContent(j,0.)
        statUps[i].Write()
        statDowns[i].Write()
        histPdf = ROOT.RooDataHist(newname,newname,obs,histos[i])
        #UP stats of MCs
        RooStatsUp = ROOT.RooDataHist('%sCMS_vhbb_stats_%s_%sUp'%(newname,newname,options[10]),'%sCMS_vhbb_stats_%s_%sUp'%(newname,newname,options[10]),obs, statUps[i])
        #DOWN stats of MCs
        RooStatsDown = ROOT.RooDataHist('%sCMS_vhbb_stats_%s_%sDown'%(newname,newname,options[10]),'%sCMS_vhbb_stats_%s_%sDown'%(newname,newname,options[10]),obs, statDowns[i])
        getattr(WS,'import')(histPdf)
        getattr(WS,'import')(RooStatsUp)
        getattr(WS,'import')(RooStatsDown)
        
    #And now WeightF sys
    if weightF_sys:
        weightF_sys_Downs[i].SetName('%sUEPSDown'%(newname))
        weightF_sys_Ups[i].SetName('%sUEPSUp'%(newname))
        weightF_sys_Ups[i].Write()
        weightF_sys_Downs[i].Write()    
        RooWeightFUp = ROOT.RooDataHist('%sUEPSUp'%(newname),'%sUEPSUp'%(newname),obs, weightF_sys_Ups[i])
        RooWeightFDown = ROOT.RooDataHist('%sUEPSDown'%(newname),'%sUEPSDown'%(newname),obs, weightF_sys_Downs[i])
        getattr(WS,'import')(RooWeightFUp)
        getattr(WS,'import')(RooWeightFDown)
    #And now Additional sample sys
    if addSample_sys:
        aSample_sys_Downs.append(aSampleUp[i].Clone())
        aSample_sys_Ups.append(aSampleDown[i].Clone())
        aSample_sys_Downs[i].SetName('%sCMS_vhbb_model_%sDown'%(newname,newname))
        aSample_sys_Ups[i].SetName('%sCMS_vhbb_model_%sUp'%(newname,newname))
        aSample_sys_Ups[i].Write()
        aSample_sys_Downs[i].Write()    
        RooSampleUp = ROOT.RooDataHist('%sCMS_vhbb_model_%sUp'%(newname,newname),'%sCMS_vhbb_model_%sUp'%(newname,newname),obs, aSample_sys_Ups[i])
        RooSampleDown = ROOT.RooDataHist('%sCMS_vhbb_model_%sDown'%(newname,newname),'%sCMS_vhbb_model_%sDown'%(newname,newname),obs, aSample_sys_Downs[i])
        getattr(WS,'import')(RooSampleUp)
        getattr(WS,'import')(RooSampleDown)


#HISTOGRAMM of DATA    
d1 = datas[0]
if len(datas)>1:
    for i in range(1,len(datas)):
        d1.Add(datas[i],1)
printc('green','','\nDATA integral = %s\n'%d1.Integral())
flow = d1.GetEntries()-d1.Integral()
if flow > 0:
    printc('red','','U/O flow: %s'%flow)
d1.SetName(Dict['Data'])
outfile.cd()
outfile.cd(Datacardbin)
#d1.Write()


if blind:
    print 'toy data integral: %s'%hDummy.Integral() 
    hDummy.SetName(Dict['Data'])
    histPdf = ROOT.RooDataHist(Dict['Data'],Dict['Data'],obs,hDummy)
    #rooDummy = ROOT.RooDataHist('data_obs','data_obs',obs,hDummy)
    #toy = ROOT.RooHistPdf('data_obs','data_obs',ROOT.RooArgSet(obs),rooDummy)
    #rooDataSet = toy.generate(ROOT.RooArgSet(obs),int(d1.Integral()))
    #histPdf = ROOT.RooDataHist('data_obs','data_obs',ROOT.RooArgSet(obs),rooDataSet.reduce(ROOT.RooArgSet(obs)))
    hDummy.Write()
else:
    histPdf = ROOT.RooDataHist(Dict['Data'],Dict['Data'],obs,d1)
    d1.Write()
#ROOT.RooAbsData.plotOn(histPdf,frame)
getattr(WS,'import')(histPdf)

#SYSTEMATICS:
UD = ['Up','Down']
systhistosarray=[]
Coco=0 #iterates over (all systematics) * (up,down)
nominalShape = options[0]
    
for sys in systematics:
    for Q in UD: # Q = 'Up' and 'Down'
        #options[7] ist der CutString name
        new_cut=sys_cut_suffix[sys]
        new_options = copy(options)
        if not new_cut == 'nominal':
            old_str,new_str=new_cut.split('>')
            new_options[7]=[options[7],old_str,new_str.replace('?',Q)]
        ff=options[0].split('.')
        if bdt == True:
            #options[0] ist die treeVar
            ff[1]='%s_%s'%(sys,Q.lower())
            new_options[0]=nominalShape.replace('.nominal','.%s_%s'%(sys,Q.lower()))
        elif mjj == True:
            if sys == 'JER' or sys == 'JES':
                ff[0]='H_%s'%(sys)
                ff[1]='mass_%s'%(Q.lower())
                new_options[0]='.'.join(ff)
            else: pass

        print '\n'
        printc('blue','','\t--> doing systematic %s %s'%(sys,Q.lower())) 

        systhistosarray.append([])
        typsX = []

        for job in info:
            if eval(job.active):
                if job.subsamples:
                    for subsample in range(0,len(job.subnames)):
                        if job.subnames[subsample] in BKGlist:
                            hTemp, typ = getHistoFromTree(job,path,config,new_options,MC_rescale_factor,subsample)
                            systhistosarray[Coco].append(myBinning.rebin(hTemp))
                            typsX.append(Group[job.subnames[subsample]])
                        elif job.subnames[subsample] == SIG:
                            hTemp, typ = getHistoFromTree(job,path,config,new_options,MC_rescale_factor,subsample)
                            systhistosarray[Coco].append(myBinning.rebin(hTemp))
                            typsX.append(Group[job.subnames[subsample]])
                            
                else:
                    if job.name in BKGlist:
                        hTemp, typ = getHistoFromTree(job,path,config,new_options,MC_rescale_factor)
                        systhistosarray[Coco].append(myBinning.rebin(hTemp))
                        typsX.append(Group[job.name])
                    elif job.name == SIG:
                        hTemp, typ = getHistoFromTree(job,path,config,new_options,MC_rescale_factor)
                        systhistosarray[Coco].append(myBinning.rebin(hTemp))
                        typsX.append(Group[job.name])

        MC_integral=0
        for histoX in systhistosarray[Coco]:
            MC_integral+=histoX.Integral()
        printc('green','', 'MC integral = %s'%MC_integral)  
        systhistosarray[Coco], typsX = orderandadd(systhistosarray[Coco],typsX,setup)

        if scaling: #rescaling after the sys has been propagated through the BDT with a scaling
            for i in range(0,len(systhistosarray[Coco])):
                for bin in range(0,histos[i].GetSize()):
                    A=systhistosarray[Coco][i].GetBinContent(bin)
                    B=histos[i].GetBinContent(bin)
                    systhistosarray[Coco][i].SetBinContent(bin,B+((A-B)/4.))
        # finaly lpop over histos
        for i in range(0,len(systhistosarray[Coco])):
            systhistosarray[Coco][i].SetName('%s%s%s'%(Dict[typs[i]],systematicsnaming[sys],Q))
            outfile.cd()
            outfile.cd(Datacardbin)
            systhistosarray[Coco][i].Write()            
            histPdf = ROOT.RooDataHist('%s%s%s'%(Dict[typs[i]],systematicsnaming[sys],Q),'%s%s%s'%(Dict[typs[i]],systematicsnaming[sys],Q),obs,systhistosarray[Coco][i])
            getattr(WS,'import')(histPdf)
        Coco+=1
WS.writeToFile(outpath+'vhbb_WS_'+ROOToutname+'.root')


# -------------------- write DATAcard: ----------------------------------------------------------------------
DCprocessseparatordict = {'WS':':','TH':'/'}
for DCtype in ['WS','TH']:
    columns=len(setup)
    #if '8TeV' in options[10]:
    #    pier = open(vhbbpath+'/python/pier8TeV.txt','r')
    #else:
    #    pier = open(vhbbpath+'/python/pier.txt','r')
    #scalefactors=pier.readlines()
    #pier.close()
    f = open(outpath+'vhbb_DC_%s_%s.txt'%(DCtype,ROOToutname),'w')
    f.write('imax\t1\tnumber of channels\n')
    f.write('jmax\t%s\tnumber of backgrounds (\'*\' = automatic)\n'%(columns-1))
    f.write('kmax\t*\tnumber of nuisance parameters (sources of systematical uncertainties)\n\n')
    f.write('shapes * * vhbb_%s_%s.root $CHANNEL%s$PROCESS $CHANNEL%s$PROCESS$SYSTEMATIC\n\n'%(DCtype,ROOToutname,DCprocessseparatordict[DCtype],DCprocessseparatordict[DCtype]))
    f.write('bin\t%s\n\n'%Datacardbin)
    if blind:
        f.write('observation\t%s\n\n'%(hDummy.Integral()))
    else:
        f.write('observation\t%s\n\n'%(int(d1.Integral())))

    f.write('bin')
    for c in range(0,columns): f.write('\t%s'%Datacardbin)
    f.write('\n')

    f.write('process')
    for c in setup: f.write('\t%s'%Dict[c])
    f.write('\n')

    f.write('process')
    for c in range(0,columns): f.write('\t%s'%c)
    f.write('\n')

    f.write('rate')
    for c in range(0,columns): f.write('\t%s'%histos[c].Integral())
    f.write('\n')

    InUse=eval(config.get('Datacard','InUse_%s'%pt_region))
    #Parse from config
    for item in InUse:
        f.write(item)
        what=eval(config.get('Datacard',item))
        f.write('\t%s'%what['type'])
        for c in setup:
            if c in what:
                if item == 'CMS_eff_e' and 'Zmm' in options[10]: f.write('\t-')
                elif item == 'CMS_eff_m' and 'Zee' in options[10]: f.write('\t-')
                elif item == 'CMS_trigger_e' and 'Zmm' in options[10]: f.write('\t-')
                elif item == 'CMS_trigger_m' and 'Zee' in options[10]: f.write('\t-')
                else:
                    f.write('\t%s'%what[c])
            else:
                f.write('\t-')
        f.write('\n')

    #Write shape stats and sys
    if binstat:
        for c in setup:
            for bin in range(0,nBins):
                f.write('CMS_vhbb_stats_%s_%s_%s\tshape'%(Dict[c], bin, options[10]))
                for it in range(0,columns):
                    if it == setup.index(c):
                        f.write('\t1.0')
                    else:
                        f.write('\t-')
                f.write('\n')

    else:
        for c in setup:
            f.write('CMS_vhbb_stats_%s_%s\tshape'%(Dict[c], options[10]))
            for it in range(0,columns):
                if it == setup.index(c):
                    f.write('\t1.0')
                else:
                    f.write('\t-')
            f.write('\n')
        
    if weightF_sys:
        f.write('UEPS\tshape')
        for it in range(0,columns): f.write('\t1.0')
        f.write('\n')

    if addSample_sys:
        alreadyAdded = []
        for newSample in addSample_sys.iterkeys():
            for c in setup:
                if not c == Group[newSample]: continue
                if Dict[c] in alreadyAdded: continue
                f.write('CMS_vhbb_model_%s\tshape'%(Dict[c]))
                for it in range(0,columns):
                    if it == setup.index(c):
                         f.write('\t1.0')
                    else:
                         f.write('\t-')
                f.write('\n')
                alreadyAdded.append(Dict[c])
        
    for sys in systematics:
        sys_factor=sys_factor_dict[sys]
        f.write('%s\tshape'%systematicsnaming[sys])
        for c in setup:
            if c in sys_affecting[sys]:
                f.write('\t%s'%sys_factor)
            else:
                f.write('\t-')
        f.write('\n')
    f.close()
outfile.Close()
