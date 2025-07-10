BEGIN{miny=100;}{count+=1; sum+=$2; sqsum+=$2*$2; if($2<miny)miny=$2; if($2>maxy)maxy=$2;}END{mean=sum/count; stdev=sqrt(sqsum/count - mean * mean); print count, sum, sqsum, miny, maxy, mean, stdev}
				  
