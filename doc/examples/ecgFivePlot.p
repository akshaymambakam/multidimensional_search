set terminal wxt size 1024,1024
set key font ",16"
set multiplot layout 3,1 rowsfirst
set lmargin at screen 0.05
#set xrange[3000:]
plot "ecg_fiveDays.txt" with steps title "predicted label"
plot "ecg_five.txt" with steps title "correct label"
plot "ecg_in.txt" with steps title "ecg signal"
#set yrange[-0.5:1.5]
#plot "ecg_sigTwo.txt" with steps title "signal > 2"
#plot "ecg_sigThree.txt" with steps title "signal > 3"
pause -1