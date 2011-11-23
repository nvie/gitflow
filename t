awk '
BEGIN{total=0;}
/feature\/test/ { 
    if ($2=="START" || $2=="UNPAUSE") {
        start=$1;
    }

    if ($2=="PAUSE" || $2=="FINISH") {
        if (start) {
            total+=$1-start; 
        }
        start = 0;
    }
}
END{print "total" total/60 " Minutes";}' .gitflowTiming 
