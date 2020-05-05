set terminal wxt size 1024,512
set xrange[x:y]
set yrange[:]
set key font ",16"
#set multiplot layout 3,1 rowsfirst
plot plot1 with steps title "predicted label" lt rgb "red" ,  \
 plot2 with steps title "correct label" lt rgb "blue", \
 "ecg_in.txt" with steps title "ECG 221" lt rgb "black"
pause -1