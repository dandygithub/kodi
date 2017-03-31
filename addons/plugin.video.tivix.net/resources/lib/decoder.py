# -*- coding: utf-8 -*-
import os

def decoder(w,i,s,e):
	A1=0
	A2=0
	A3=0
	L1=[]
	L2=[]

	while True:
		if A1<5: L2.append(w[A1])
		elif A1<len(w): L1.append(w[A1])
		A1+=1
		
		if A2<5: L2.append(i[A2])
		elif A2<len(i): L1.append(i[A2])
		A2+=1
		
		if A3<5: L2.append(s[A3])
		elif A3<len(s): L1.append(s[A3])
		A3+=1
		
		if(len(w)+len(i)+len(s)+len(e)==len(L1)+len(L2)+len(e)): break

	B1=''.join(L1)
	B2=''.join(L2)
	A2=0
	A1=0
	L3=[]
	while A1<len(L1):
		C1=-1
		if ord(B2[A2])%2: C1=1
		L3.append(unichr(int(B1[A1:A1+2],36)-C1))
		A2+=1
		if A2>=len(L2):A2=0
		A1+=2
	
	return u''.join(L3)

def decoder2(w,i,s,e):
    s = 0
    st = ''
    while s<len(w):
        st += unichr(int(w[s:s+2],36))
        s += 2
    return st

#;eval(function(w,i,s,e){
#for(s=0;s<w.length;s+=2){
#  i+=String.fromCharCode(parseInt(w.substr(s,2),36));
#}
#return i;
#}
#('1b1b0d0a1n2t3a2p30142u39322r382x3332143b182x1837182t153f2u333614371p1c1n371o3b1a302t322v382w1n37171p1e153f2x171p2b38362x322v1a2u3633311v2w2p361v332s2t14342p36372t213238143b1a37392q3738361437181e15181f1i15151n3h362t383936320w2x1n3h14131d2q1d2q1c2s1c2p1318131318131318131315151n1n2t3a2p30142u39322r382x3332143b182x1837182t153f2u333614371p1c1n371o3b1a302t322v382w1n37171p1e153f2x171p2b38362x322v1a2u3633311v2w2p361v332s2t14342p36372t213238143b1a37392q3738361437181e15181f1i15151n3h362t383936320w2x1n3h14131d2q1d2q1c2s1c2p1d321e381f2p1e341f1c1d1g1e391f1l1f1e1e361f1k1e3c1f1f1f1e1d1g1f2q1d1k1e3c1d1k1f1j1d1k1e381d1h1f2u1e391f1f1f1i1d1g1f1j1d341d2r1d321f1j1d331f2q1d2p1f1c1e381f1e1e3a1f1k1e3b1d321f1j1d1j1d341d2t1d1h1f2u1e3c1d1j1d341e2q1f1k1f1i1e3c1f1e1e3a1d2p1e391f1i1f1f1f1d1d3a1e3b1e341f1i1d3a1f1f1e371e381d1g1f1g1e341f1i1f1j1e381e1d1f1e1f1k1d1g1f2q1d2p1f1j1f1l1e351f1j1f1k1f1i1d1g1f1j1d1k1d2t1d1h1d1k1d2u1d2x1d1h1d1h1d321f2w1f1i1e381f1k1f1l1f1i1f1e1c3b1e3c1d321f2w1d1g1d1f1d2s1e351d2s1e351d2r1e371d2r1e341d1f1d1k1d1f1d1f1d1k1d1f1d1f1d1k1d1f1d1f1d1h1d1h1d321318131318131318131315151n','','',''));; ;eval(function(w,i,s,e){var lIll=0;var ll1I=0;var Il1l=0;var ll1l=[];var l1lI=[];while(true){if(lIll<5)l1lI.push(w.charAt(lIll));else if(lIll<w.length)ll1l.push(w.charAt(lIll));lIll++;if(ll1I<5)l1lI.push(i.charAt(ll1I));else if(ll1I<i.length)ll1l.push(i.charAt(ll1I));ll1I++;if(Il1l<5)l1lI.push(s.charAt(Il1l));else if(Il1l<s.length)ll1l.push(s.charAt(Il1l));Il1l++;if(w.length+i.length+s.length+e.length==ll1l.length+l1lI.length+e.length)break;}var lI1l=ll1l.join('');var I1lI=l1lI.join('');ll1I=0;var l1ll=[];for(lIll=0;lIll<ll1l.length;lIll+=2){var ll11=-1;if(I1lI.charCodeAt(ll1I)%2)ll11=1;l1ll.push(String.fromCharCode(parseInt(lI1l.substr(lIll,2),36)-ll11));ll1I++;if(ll1I>=l1lI.length)ll1I=0;}return l1ll.join('');}('33f8b3q012c2e122b3b322v3w24112o241v392215312s0c3b1x1y2c11113s2q233c1z0x1g2531142t211o162137211g273x2a1735141i12313s181627353519293l1k1c1b1g1l1l101y2u103l301a2c212j3r2e1b2e181b1l2x102j1w2d2r1o1t1d1g1k1h1i1e1m1d2b3i282u2f17123x2g3q1c1f2b361q1m','7ab1db3x1z3z2o3y2d221w1a3t3b3q3w39383q29232q1z3c07041z3e3e153z2s0c3b1x143o01141w1z0o143q251z1m3x3c3s0w32141o03132c341m1o3516241x331a191d1f1d1b1a1c3t39181a3u3x2u1q2c3f2g3a2k2j2w361d1c2v172w1h1b1g1i2h1b1h1j2f1f25193v2c3c2e2b203q292g2y372c1q14','cb5d7273c111z193y1q1o23233c32293124333s3u3o253c1x0z0o113139252q1z3c0706393x3q1m253w141g3s35343934013x3535163z103o271g1939123s14371c1i1f1e191l1c3f232b3g1q38392w3q1d223h232e2a371e1w2x141j2w2e2f2b1g1u1h1k1h1s1i1r1h2d3d171h2d3r182b2e1t2d222u121','334ff177903c72644e82a06d97c36bfe'));

#function(w,i,s,e){
#var lIll=0;
#var ll1I=0;
#var Il1l=0;
#var ll1l=[];
#var l1lI=[];
#while(true){
#if(lIll<5)
#l1lI.push(w.charAt(lIll));
#else if(lIll<w.length) 
#ll1l.push(w.charAt(lIll));
#lIll++;
#if(ll1I<5)
#l1lI.push(i.charAt(ll1I));
#else if(ll1I<i.length)
#ll1l.push(i.charAt(ll1I));
#ll1I++;
#if(Il1l<5)
#l1lI.push(s.charAt(Il1l));
#else if(Il1l<s.length)
#ll1l.push(s.charAt(Il1l));
#Il1l++;
#if(w.length+i.length+s.length+e.length==ll1l.length+l1lI.length+e.length)
#break;
#}
#var lI1l=ll1l.join('');
#var I1lI=l1lI.join('');
#ll1I=0;
#var l1ll=[];
#for(lIll=0;lIll<ll1l.length;lIll+=2){
#var ll11=-1;
#if(I1lI.charCodeAt(ll1I)%2)
#ll11=1;
#l1ll.push(String.fromCharCode(parseInt(lI1l.substr(lIll,2),36)-ll11));
#ll1I++;
#if(ll1I>=l1lI.length)ll1I=0;
#}
#return l1ll.join('');
#}