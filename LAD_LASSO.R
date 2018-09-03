library(flare)


bosdata <- read.csv("/opt/school/subway/gendata/boston_stations.csv", header= TRUE, sep  = ",", quote = '"', stringsAsFactors=FALSE)
bosride <- read.csv("/opt/school/subway/gendata/boston_subway_ridership.csv", header = FALSE, sep = ";", quote="'", stringsAsFactors=FALSE)
colnames(bosride) <- c("name", "ridership")
bosdata <- merge(bosdata, bosride, by="name")
#print(subset(bosdata, select=c("name", "ridership", "near_population", "near_employment")))

chidata <- read.csv("/opt/school/subway/gendata/chicago_stations.csv", header= TRUE, sep  = ",", quote = '"', stringsAsFactors=FALSE)
chiride <- read.csv("/opt/school/subway/gendata/chicago_subway_ridership.csv", header = FALSE, sep = ";", quote="'", stringsAsFactors=FALSE)
colnames(chiride) <- c("name", "ridership")
chidata <- merge(chidata, chiride, by="name")
#print(subset(chidata, select=c("name", "ridership", "near_population", "near_employment")))

ladata <- read.csv("/opt/school/subway/gendata/la_stations.csv", header= TRUE, sep  = ",", quote = '"', stringsAsFactors=FALSE)
laride <- read.csv("/opt/school/subway/gendata/la_subway_ridership.csv", header = FALSE, sep = ";", quote="'", stringsAsFactors=FALSE)
colnames(laride) <- c("name", "ridership")
ladata <- merge(ladata, laride, by="name")
ladata <- ladata[!(ladata$name %in% c("Willowbrook-Rosa Parks", "Union Station", "7th Street-Metro Center")),]
#print(subset(ladata, select=c("name", "ridership")))

atldata <- read.csv("/opt/school/subway/gendata/atlanta_stations.csv", header= TRUE, sep  = ",", quote = '"', stringsAsFactors=FALSE)
atlride <- read.csv("/opt/school/subway/gendata/atlanta_subway_ridership.csv", header = FALSE, sep = ";", quote="'", stringsAsFactors=FALSE)
colnames(atlride) <- c("name", "ridership")
atldata <- merge(atldata, atlride, by="name")
atldata <- atldata[!(atldata$name=='Five Points'),]
#print(subset(atldata, select=c("name", "ridership", "near_population", "near_employment")))

daldata <- read.csv("/opt/school/subway/gendata/dallas_stations.csv", header= TRUE, sep  = ",", quote = '"', stringsAsFactors=FALSE)
dalride <- read.csv("/opt/school/subway/gendata/dallas_subway_ridership.csv", header = FALSE, sep = ";", quote="'", stringsAsFactors=FALSE)
colnames(dalride) <- c("name", "ridership")
daldata <- merge(daldata, dalride, by="name")
daldata <- daldata[!(daldata$name=='Union Station'),]
#print(subset(daldata, select=c("name", "ridership", "near_population", "near_employment")))

dendata <- read.csv("/opt/school/subway/gendata/denver_stations.csv", header= TRUE, sep  = ",", quote = '"', stringsAsFactors=FALSE)
denride <- read.csv("/opt/school/subway/gendata/denver_subway_ridership.csv", header = FALSE, sep = ";", quote="'", stringsAsFactors=FALSE)
colnames(denride) <- c("name", "ridership")
dendata <- merge(dendata, denride, by="name")
dendata <- dendata[!(dendata$name=='Union Station'),]
#print(subset(dendata, select=c("name", "ridership", "near_population", "near_employment")))

xalldata = rbind(bosdata, chidata, ladata, atldata, daldata, dendata)
yalldata = xalldata[, "ridership"]
xalldata = xalldata[, !(names(xalldata) %in% c("name", "ridership", "lat", "lon", 'X30net_students', 'X15net_students', 'near_students'))]
cvvector = rbind(matrix(1,113,1), matrix(2,138,1), matrix(3, 78, 1), matrix(4, 38, 1), matrix(5, 61, 1), matrix(6, 44, 1))




xbos = bosdata[, !(names(bosdata) %in% c("name", "ridership", "lat", "lon", 'X30net_students', 'X15net_students', 'near_students'))]
ybos = bosdata[, "ridership"]
xbos = xbos / sum(ybos)

xchi = chidata[, !(names(chidata) %in% c("name", "ridership", "lat", "lon", 'X30net_students', 'X15net_students', 'near_students'))]
ychi = chidata[, "ridership"]
xchi = xchi / sum(ychi)

xla = ladata[, !(names(ladata) %in% c("name", "ridership", "lat", "lon", 'X30net_students', 'X15net_students', 'near_students'))]
yla = ladata[, "ridership"]
xla = xla / sum(yla)

xatl = atldata[, !(names(chidata) %in% c("name", "ridership", "lat", "lon", 'X30net_students', 'X15net_students', 'near_students'))]
yatl = atldata[, "ridership"]
xatl = xatl / sum(yatl)

xdal = daldata[, !(names(daldata) %in% c("name", "ridership", "lat", "lon", 'X30net_students', 'X15net_students', 'near_students'))]
ydal = daldata[, "ridership"]
xdal = xdal / sum(ydal)

xden = dendata[, !(names(dendata) %in% c("name", "ridership", "lat", "lon", 'X30net_students', 'X15net_students', 'near_students'))]
yden = dendata[, "ridership"]
xden = xden / sum(yden)


xnotbos = rbind(xchi, xla, xatl, xdal, xden)
ynotbos = c(ychi, yla, yatl, ydal, yden)

xnotchi = rbind(xbos, xla, xatl, xdal, xden)
ynotchi = c(ybos, yla, yatl, ydal, yden)

xnotla = rbind(xbos, xchi, xatl, xdal, xden)
ynotla = c(ybos, ychi, yatl, ydal, yden)

xnotatl = rbind(xbos, xchi, xla, xdal, xden)
ynotatl = c(ybos, ychi, yla, ydal, yden)

xnotdal = rbind(xbos, xchi, xla, xatl, xden)
ynotdal = c(ybos, ychi, yla, yatl, yden)

xnotden = rbind(xbos, xchi, xla, xatl, xdal)
ynotden = c(ybos, ychi, yla, yatl, ydal)


getErrs <- function(predicted, actual) {
  SysErr = (abs(sum(predicted) - sum(actual)))/sum(actual)
  StaErr = sum(abs(predicted - actual))/sum(actual)
  print("System Error")
  print(SysErr)
  print("Station Error")
  print(StaErr) 
}

colSd <- function (x, na.rm=FALSE) apply(X=x, MARGIN=2, FUN=sd, na.rm=na.rm)

ynot = data.matrix(ynotbos)
xnot = data.matrix(xnotbos)
y = data.matrix(ybos)
x = data.matrix(xbos)

#print(x[, c(1,2,3,4,5)])

#min/max scale
#mins = apply(xnot, 2, min)
#maxs = apply(xnot, 2, max)
#print(mins[c(1,2,3,4,5)])
#print(maxs[c(1,2,3,4,5)])
#xnot = sweep(sweep(xnot, 2, mins),2,(maxs - mins),  "/")
#x = sweep(sweep(x, 2, mins),2,(maxs - mins),  "/")

#normalize scale
mn <- colMeans(xnot)
std <- colSd(xnot)
#print(mn[c(1,2,3,4,5)])
#print(std[c(1,2,3,4,5)])
xnot = sweep(sweep(xnot, 2, mn), 2, std, "/")
x = sweep(sweep(x, 2, mn), 2, std, "/")



#print("Source Data")
#print(xnotden)
#print(ynotden)
#print(xden)
#print(yden)
#print(colnames(x))
#print(x[, c(1,2,3,4,5)])
#print(y)

lvec = seq(0, -4, -0.5)
elvec = exp(lvec)

print("First round")
print(lvec)


fit = slim(xnot, ynot, lambda = elvec, q=1)   #Two here
results = x %*% fit$beta                    # One here
syserrs = abs(colSums(results) - sum(y))/sum(y)
staerrs = colSums(abs(sweep(results, 1, y)))/sum(y)
print(syserrs)
print(staerrs)
print(syserrs + staerrs)
idx  = which.min(syserrs + staerrs)
print(idx)

#idx = 9

lvec = seq(lvec[idx]+0.5, lvec[idx]-0.5, -.1)
elvec = exp(lvec)
print("Second round")
print(lvec)

fit = slim(xnot, ynot, lambda = elvec, q=1)    # Two here
results = x %*% fit$beta          # One here
syserrs = abs(colSums(results) - sum(y))/sum(y)
staerrs = colSums(abs(sweep(results, 1, y)))/sum(y)
print(syserrs)
print(staerrs)
print(syserrs + staerrs)
idx  = which.min(syserrs + staerrs)
print(idx)

params = data.matrix(fit$beta[, idx])
print(params)

results = x %*% params       # One here
getErrs(results, y)                  # One here





