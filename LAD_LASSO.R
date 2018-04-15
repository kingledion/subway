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
xalldata = xalldata[, !(names(xalldata) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
cvvector = rbind(matrix(1,113,1), matrix(2,138,1), matrix(3, 78, 1), matrix(4, 38, 1), matrix(5, 61, 1), matrix(6, 44, 1))


xnotbos = rbind(chidata, ladata, atldata, daldata, dendata)
ynotbos = xnotbos[, "ridership"]
xnotbos = xnotbos[, !(names(xnotbos) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
xnotchi = rbind(bosdata,ladata, atldata, daldata, dendata)
ynotchi = xnotchi[, "ridership"]
xnotchi = xnotchi[, !(names(xnotchi) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
xnotla = rbind(bosdata, chidata, atldata, daldata, dendata)
ynotla = xnotla[, "ridership"]
xnotla = xnotla[, !(names(xnotla) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
xnotatl = rbind(bosdata, chidata, ladata, daldata, dendata)
ynotatl = xnotatl[, "ridership"]
xnotatl = xnotatl[, !(names(xnotatl) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
xnotdal = rbind(bosdata, chidata, ladata, atldata, dendata)
ynotdal = xnotdal[, "ridership"]
xnotdal = xnotdal[, !(names(xnotdal) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
xnotden = rbind(bosdata, chidata, ladata, atldata, daldata)
ynotden = xnotden[, "ridership"]
xnotden = xnotden[, !(names(xnotden) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]


xbos = bosdata[, !(names(bosdata) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
ybos = bosdata[, "ridership"]
xchi = chidata[, !(names(chidata) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
ychi = chidata[, "ridership"]
xla = ladata[, !(names(ladata) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
yla = ladata[, "ridership"]
xatl = atldata[, !(names(chidata) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
yatl = atldata[, "ridership"]
xdal = daldata[, !(names(daldata) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
ydal = daldata[, "ridership"]
xden = dendata[, !(names(dendata) %in% c("name", "ridership", "lat", "lon", '30net_students', '15net_students', 'near_students'))]
yden = dendata[, "ridership"]


getErrs <- function(predicted, actual) {
  SysErr = (abs(sum(predicted) - sum(actual)))/sum(actual)
  StaErr = sum(abs(predicted - actual))/sum(actual)
  print(Sta)
  print(SysErr) 
}

lvec = seq(5, -6, -1)


#print(lvec)


fit = slim(data.matrix(xnotdal), data.matrix(ynotdal), lambda = lvec, q=1)   #Two here
results = data.matrix(xnotdal) %*% fit$beta                    # One here
errs = sweep(results, 1, data.matrix(ynotdal))                # One here
print(colSums(errs))
idx  = which.min(abs(colSums(errs)))
print(idx)

#idx = 4

lvec = seq(idx-2, idx, 0.25)
lvec = exp(-lvec)

fit = slim(data.matrix(xnotdal), data.matrix(ynotdal), lambda = lvec, q=1)    # Two here
results = data.matrix(xnotdal) %*% fit$beta          # One here
errs = sweep(results, 1, data.matrix(ynotdal))      # One here
print(colSums(errs))
idx  = which.min(abs(colSums(errs)))
print(idx)

print(data.matrix(fit$beta[, idx]))

results = data.matrix(xdal) %*% fit$beta       # One here
getErrs(results[, idx], ydal)                  # One here



