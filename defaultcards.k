*KEYWORD  
*CONTROL_TERMINATION
$#  endtim    endcyc     dtmin    endeng    endmas     nosol     
     180.0         0       0.0       0.01.000000E8         0
*DATABASE_BNDOUT
$#      dt    binary      lcur     ioopt
       1.0         1         0         1
*DATABASE_GLSTAT
$#      dt    binary      lcur     ioopt     
       1.0         0         0         1
*DATABASE_NODOUT
$#      dt    binary      lcur     ioopt     
       1.0         0         0         1
*DATABASE_HISTORY_NODE
        37
*DATABASE_BINARY_D3PLOT
$#      dt      lcdt      beam     npltc    psetid      
       5.0         0         0         0         0
$#   ioopt     
         0
*PART
$#                                                                         title
BeamPart
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         1         1         1         0         0         0         0         0
*SECTION_BEAM_TITLE
Beam
$#   secid    elform      shrf   qr/irid       cst     scoor       nsm   
         1         1      0.83         5         1       0.0       0.0
$#     ts1       ts2       tt1       tt2     nsloc     ntloc     
       0.1       0.1       0.0       0.0       0.0       0.0
*MAT_ELASTIC_TITLE
PLA
$#     mid        ro         e        pr        da        db  not used        
         1    1250.0  3500.0e6      0.36       0.0       0.0       0.0
*DEFINE_CURVE_TITLE
ConstantVelocity
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
         1         0       1.0       1.0       0.0       0.0         0         0
$#                a1                  o1  
                 0.0                 0.1
               180.0                 0.1
               180.1                -0.1
               360.0                -0.1
*DAMPING_GLOBAL
$#    lcid    valdmp       stx       sty       stz       srx       sry       srz
         0       1.0       0.0       0.0       0.0       0.0       0.0       0.0   
         