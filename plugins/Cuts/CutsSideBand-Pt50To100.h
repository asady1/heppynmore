#ifndef CUTSSIDEBAND_H
#define CUTSSIDEBAND_H
#include "../../interface/CutsAndHistos.h"
#include "../../interface/ntupleReader.hpp"
#include <TH1F.h>
#include <sstream>
#include "../../interface/samples.hpp"
#include "TKey.h"

#define CSVM 0.679
#define CSVC 0.5 //custom btag
#define CSVL 0.244
#define CSVT 0.898
#define fA 0.46502
#define fB 0.53498

// New implementations of the control region
// The signal regions must be implemented incrementally since cutflow is needed

bool sCut( ntupleReader & p , Sample & sample ){
  return ( sampleCut && p.EVENT_json == true && p.hbhe == true );
};

std::string generateName( std::string & baseName, int ch = -1, int btag = 0, int jec = 0 ) {
  std::string channel; 
  if(ch == -1)
    channel = "HZcomb";
  else if(ch == 0)
    channel = "HZmm";
  else if(ch == 1)
    channel = "HZee";
  if( jec == 1 )
    return ( "SystJecUP"+baseName+channel );
  else if( jec == -1 )
    return ( "SystJecDOWN"+baseName+channel );
  else if( jec == 2 )
    return ( "SystJerUP"+baseName+channel );
  else if( jec == -2 )
    return ( "SystJerDOWN"+baseName+channel );
  if( btag == 1)
    return ( "SystBtagUP"+baseName+channel );
  else if( btag == -1 )
    return ( "SystBtagDOWN"+baseName+channel );
  else if( btag == 2 )
    return ( "SystBtagFUP"+baseName+channel );
  else if( btag == -2 )
    return ( "SystBtagFDOWN"+baseName+channel );
  else if( btag == 0 && jec == 0)
    return baseName+channel;
};


Bool_t channel(ntupleReader & p, int ch = -1){
  bool trigger[2];
  //muons
  trigger[0] = ( ( (((p.EVENT_run<173198 && (p.triggerFlags[0]>0 || p.triggerFlags[13]>0 || p.triggerFlags[14]>0 || p.triggerFlags[20]>0 || p.triggerFlags[21]>0)) || (p.EVENT_run>=173198 && p.EVENT_run<175832  && (p.triggerFlags[13]>0 ||p.triggerFlags[14]>0 || p.triggerFlags[22]>0 || p.triggerFlags[23]>0))|| (p.EVENT_run>=175832 && p.EVENT_run<178390 && (p.triggerFlags[13]>0 ||p.triggerFlags[14]>0 ||p.triggerFlags[15]>0 || p.triggerFlags[21]>0 || p.triggerFlags[22]>0 || p.triggerFlags[23]>0)) || (p.EVENT_run>=178390 && (p.triggerFlags[14]>0 ||p.triggerFlags[15]>0 || p.triggerFlags[21]>0 || p.triggerFlags[22]>0 || p.triggerFlags[23]>0 || p.triggerFlags[24]>0 || p.triggerFlags[25]>0 || p.triggerFlags[26]>0 || p.triggerFlags[27]>0)))) ) );
  //electrons
  trigger[1] = ( ( p.triggerFlags[5] || p.triggerFlags[6] ) );

  if(ch == -1) return (( p.Vtype == 0 && trigger[0] ) || ( p.Vtype == 1 && trigger[1] )); 
  else return ( p.Vtype == ch && trigger[ch] );
};

double w(ntupleReader &p, Sample &sample){
  std::string DY("DY");
  if(sample.name == DY) return (p.lheWeight); 
  else return 1;
};

class BDTTrainingRegion: public CutSample{
 public:
  BDTTrainingRegion(int ch_= -1, int jec_= 0 , int btag_ = 0):
   ch(ch_),jec(jec_),btag(btag_){ baseName = "BDTTrainingRegion"; };
  Bool_t pass(ntupleReader &p){
    return ( p.hJet_PT(0,jec) > 20.  
	     && p.hJet_PT(1,jec) > 20. 
	     && p.hJet_CSV(0,btag) > CSVL 
	     && p.hJet_CSV(1,btag) > CSVL 
	     //	     && p.Higgs(jec).Pt() > 100. 
	     && p.V_pt < 100. 
	     && p.V_pt > 50. 
	     && p.V_mass > 75. 
	     && p.V_mass < 105 
	     && p.Higgs(jec).M() < 250.
	     //	     && p.CountAddJets() < 2 
	     && channel( p, ch )  );
  }
  Bool_t pass(ntupleReader &p, Sample &sample){
    return ( sCut( p , sample ) == true && pass( p ) );
  }
  double weight(ntupleReader &p, Sample &sample) { return w( p, sample); }

 private:
  std::string name(){ return( generateName(baseName, ch, btag, jec) ) ;};
  std::string baseName;
  int btag;
  int jec;
  int ch;
};

class BDTSideBandRegion: public CutSample{
 public:
  BDTSideBandRegion(int ch_= -1, int jec_= 0 , int btag_ = 0):
    ch(ch_),jec(jec_),btag(btag_){ baseName = "BDTSideBandRegion"; };
  Bool_t pass(ntupleReader &p){
    return ( p.hJet_PT(0,jec) > 20.  
	     && p.hJet_PT(1,jec) > 20. 
	     && p.hJet_CSV(0,btag) > CSVL 
	     && p.hJet_CSV(1,btag) > CSVL 
	     //Loose-Custom : ONLY FOR THE FIT for Scale Factors 
	     && ( p.hJet_CSV(0,btag) > CSVC 
		  || p.hJet_CSV(1,btag) > CSVC )
	     //	     && p.Higgs(jec).Pt() > 100. 
	     && p.V_pt < 100. 
	     && p.V_pt > 50. 
	     && p.V_mass > 75. 
	     && p.V_mass < 105 
	     && ( p.Higgs(jec).M() < 80.
		  || p.Higgs(jec).M() > 150. )
	     && p.Higgs(jec).M() < 250.
	     //	     && p.CountAddJets() < 2 
	     && channel( p, ch) );
  }
  Bool_t pass(ntupleReader &p, Sample &sample){
    return ( sCut( p , sample ) == true && pass( p ) );
  }
  double weight(ntupleReader &p, Sample &sample) { return w( p, sample); }

 private:
  std::string name(){ return( generateName(baseName, ch, btag, jec) ) ;};
  std::string baseName;
  int btag;
  int jec;
  int ch;

};

class BDTSignalRegion: public CutSample{
 public:
  BDTSignalRegion( int ch_= -1,int jec_= 0 , int btag_ = 0):
    ch(ch_),jec(jec_),btag(btag_){ baseName = "BDTSignalRegion"; };
  Bool_t pass(ntupleReader &p){
    return ( p.hJet_PT(0,jec) > 20.  
	     && p.hJet_PT(1,jec) > 20. 
	     && p.hJet_CSV(0,btag) > CSVL 
	     && p.hJet_CSV(1,btag) > CSVL 
	     //	     && p.Higgs(jec).Pt() > 100. 
	     && p.V_pt < 100. 
	     && p.V_pt > 50. 
	     && p.V_mass > 75. 
	     && p.V_mass < 105 
	     && p.Higgs(jec).M() > 80.
	     && p.Higgs(jec).M() < 150.
	     //	     && p.CountAddJets() < 2 
	     && channel( p, ch) );
  }
  Bool_t pass(ntupleReader &p, Sample &sample){
    return ( sCut( p , sample ) == true && pass( p ) );
  }
  double weight(ntupleReader &p, Sample &sample) { return w( p, sample); }

 private:
  std::string name(){ return( generateName(baseName, ch, btag, jec) ) ;};
  std::string baseName;
  int btag;
  int jec;
  int ch;
};

class BDTTTbarControlRegion: public CutSample{
 public:
  BDTTTbarControlRegion(int ch_= -1, int jec_ = 0, int btag_ = 0):
    ch(ch_),jec(jec_), btag(btag_) { baseName = "BDTTTbarControlRegion"; };
  Bool_t pass(ntupleReader &p){
    return ( p.hJet_PT(0,jec) > 20. 
	     && p.hJet_PT(1,jec) > 20. 
	     && p.hJet_CSV(0,btag) > CSVL 
	     && p.hJet_CSV(1,btag) > CSVL
	     //	     && p.CountAddJets() > 0
	     // 	     && p.Higgs(jec).Pt() > 100. 
	     && p.V_pt < 100. 
	     && p.V_pt > 50. 
	     && p.V_mass > 50. 
	     && ( p.V_mass > 105.
		  || p.V_mass < 75. )
/* 	     && ( p.Higgs(jec).M() < 80. */
/* 		  || p.Higgs(jec).M() > 150. ) */
	     && p.Higgs(jec).M() < 250.
	     && channel( p, ch) );
  }
  Bool_t pass(ntupleReader &p, Sample &sample){
    return ( sCut( p, sample ) == true && pass( p ) );
  }
  double weight(ntupleReader &p, Sample &sample) { return w( p, sample); }

 private:
  std::string name() {return generateName(baseName, ch, btag, jec);};
  std::string baseName;
  int btag;
  int jec;
  int ch;
};

#endif
