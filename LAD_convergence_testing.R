library(flare)


daldata <- read.csv("/opt/school/subway/gendata/dallas_stations.csv", header= TRUE, sep  = ",", quote = '"', stringsAsFactors=FALSE)
dalride <- read.csv("/opt/school/subway/gendata/dallas_subway_ridership.csv", header = FALSE, sep = ";", quote="'", stringsAsFactors=FALSE)
colnames(dalride) <- c("name", "ridership")
daldata <- merge(daldata, dalride, by="name")


dendata <- read.csv("/opt/school/subway/gendata/denver_stations.csv", header= TRUE, sep  = ",", quote = '"', stringsAsFactors=FALSE)
denride <- read.csv("/opt/school/subway/gendata/denver_subway_ridership.csv", header = FALSE, sep = ";", quote="'", stringsAsFactors=FALSE)
colnames(denride) <- c("name", "ridership")
dendata <- merge(dendata, denride, by="name")




xdal = daldata[, (names(daldata) %in% c("near_population", "near_pop_old", "near_pop_child", "near_employment", "X15net_employment", "X15net_population", "near_business", "near_hospitality", "X30net_population"))]
ydal = daldata[, "ridership"]

xden = dendata[, (names(dendata) %in% c("near_population", "near_pop_old", "near_pop_child", "near_employment", "X15net_employment", "X15net_population", "near_business", "near_hospitality", "X30net_population"))]
yden = dendata[, "ridership"]




getErrs <- function(predicted, actual) {
  
  #print(predicted)
  #SysErr = (abs(sum(predicted) - sum(actual)))/sum(actual)
  StaErr = sum(abs(predicted - actual))/sum(actual)
  #print("System Error")
  #print(SysErr)
  print("Station Error")
  print(StaErr) 
}

colSd <- function (x, na.rm=FALSE) apply(X=x, MARGIN=2, FUN=sd, na.rm=na.rm)



#min/max scale
#mins = apply(xnot, 2, min)
#maxs = apply(xnot, 2, max)
#print(mins[c(1,2,3,4,5)])
#print(maxs[c(1,2,3,4,5)])
#xnot = sweep(sweep(xnot, 2, mins),2,(maxs - mins),  "/")
#x = sweep(sweep(x, 2, mins),2,(maxs - mins),  "/")



assessLAD <- function(xnot, ynot, x, y, lvec) {
  
  #print(xnot)
  #print(ynot)
  
  elvec = exp(lvec)
  
  fit = slim(xnot, ynot, lambda = elvec, q=1)   
  results = sweep(x %*% fit$beta, 2, fit$intercept, "+")               
  staerrs = colSums(abs(sweep(results, 1, y)))/sum(y)
  print(staerrs)
  idx  = which.min(staerrs)
  
  print("Parameters")
  params = data.matrix(fit$beta[, idx])
  intercept = data.matrix(fit$intercept[ ,idx])[1,1]
  print(intercept)
  print(params)

  
  print("Error Scores")
  predicted = x %*% params + intercept
  getErrs(predicted, y)   
  
}



print("Not normalized")

ynot = data.matrix(ydal)
xnot = data.matrix(xdal)
y = data.matrix(yden)
x = data.matrix(xden)

lvec = seq(4, -10, -0.5)

assessLAD(xnot, ynot, x, y, lvec)
  





print("Normalized")

#normalize scale
mn <- colMeans(xnot)
std <- colSd(xnot)
xnot = sweep(sweep(xnot, 2, mn), 2, std, "/")
x = sweep(sweep(x, 2, mn), 2, std, "/")

assessLAD(xnot, ynot, x, y, lvec)      






