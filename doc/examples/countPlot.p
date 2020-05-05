set terminal wxt size 1024,512
set key font ",16"
set multiplot layout 2,1 rowsfirst
set lmargin at screen 0.05
plot "ecg_cgIn.txt" with steps title "signal s" lt rgb "black", \
 "ecg_cg3.txt" with steps title "s < 3" lt rgb "red"
set yrange[-1:2]
plot "ecg_cg2.txt" with steps title "s < 2" lt rgb "blue", \
 "ecg_cg6.txt" with steps title "s < 6" lt rgb "brown"
pause -1