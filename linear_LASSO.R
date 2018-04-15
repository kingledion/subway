library(glmnet)


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
xalldata = xalldata[, !(names(xalldata) %in% c("name", "ridership", "lat", "lon"))]
cvvector = rbind(matrix(1,113,1), matrix(2,138,1), matrix(3, 78, 1), matrix(4, 38, 1), matrix(5, 61, 1), matrix(6, 44, 1))


xnotbos = rbind(chidata, ladata, atldata, daldata, dendata)
ynotbos = xnotbos[, "ridership"]
xnotbos = xnotbos[, !(names(xnotbos) %in% c("name", "ridership", "lat", "lon"))]
xnotchi = rbind(bosdata,ladata, atldata, daldata, dendata)
ynotchi = xnotchi[, "ridership"]
xnotchi = xnotchi[, !(names(xnotchi) %in% c("name", "ridership", "lat", "lon"))]
xnotla = rbind(bosdata, chidata, atldata, daldata, dendata)
ynotla = xnotla[, "ridership"]
xnotla = xnotla[, !(names(xnotla) %in% c("name", "ridership", "lat", "lon"))]
xnotatl = rbind(bosdata, chidata, ladata, daldata, dendata)
ynotatl = xnotatl[, "ridership"]
xnotatl = xnotatl[, !(names(xnotatl) %in% c("name", "ridership", "lat", "lon"))]
xnotdal = rbind(bosdata, chidata, ladata, atldata, dendata)
ynotdal = xnotdal[, "ridership"]
xnotdal = xnotdal[, !(names(xnotdal) %in% c("name", "ridership", "lat", "lon"))]
xnotden = rbind(bosdata, chidata, ladata, atldata, daldata)
ynotden = xnotden[, "ridership"]
xnotden = xnotden[, !(names(xnotden) %in% c("name", "ridership", "lat", "lon"))]


xbos = bosdata[, !(names(bosdata) %in% c("name", "ridership", "lat", "lon"))]
ybos = bosdata[, "ridership"]
xchi = chidata[, !(names(chidata) %in% c("name", "ridership", "lat", "lon"))]
ychi = chidata[, "ridership"]
xla = ladata[, !(names(ladata) %in% c("name", "ridership", "lat", "lon"))]
yla = ladata[, "ridership"]
xatl = atldata[, !(names(chidata) %in% c("name", "ridership", "lat", "lon"))]
yatl = atldata[, "ridership"]
xdal = daldata[, !(names(daldata) %in% c("name", "ridership", "lat", "lon"))]
ydal = daldata[, "ridership"]
xden = dendata[, !(names(dendata) %in% c("name", "ridership", "lat", "lon"))]
yden = dendata[, "ridership"]


getErrs <- function(predicted, actual) {
  MAPE = (abs(sum(predicted) - sum(actual)))/sum(actual)
  SSE = sum(abs(predicted - actual))/sum(actual)
  print(MAPE)
  print(SSE) 
}

print("Boston")
fit = cv.glmnet(data.matrix(xnotbos), data.matrix(ynotbos), alpha=1)
coef(fit, s="lambda.1se")

print(fit$lambda.1se)
pred = predict(fit, data.matrix(xbos), s= "lambda.1se")
getErrs(pred, ybos)



print("Chicago")
fit = cv.glmnet(data.matrix(xnotchi), data.matrix(ynotchi), alpha=1)
coef(fit, s="lambda.1se")

print(fit$lambda.1se)
pred = predict(fit, data.matrix(xchi), s= "lambda.1se")
getErrs(pred, ychi)



print("Los Angeles")
fit = cv.glmnet(data.matrix(xnotla), data.matrix(ynotla), alpha=1)
coef(fit, s="lambda.1se")

print(fit$lambda.1se)
pred = predict(fit, data.matrix(xla), s= "lambda.1se")
getErrs(pred, yla)



print("Atlanta")
fit = cv.glmnet(data.matrix(xnotatl), data.matrix(ynotatl), alpha=1)
coef(fit, s="lambda.1se")

print(fit$lambda.1se)
pred = predict(fit, data.matrix(xatl), s= "lambda.1se")
getErrs(pred, yatl)




print("Dallas")
fit = cv.glmnet(data.matrix(xnotdal), data.matrix(ynotdal), alpha=1)
coef(fit, s="lambda.1se")

print(fit$lambda.1se)
pred = predict(fit, data.matrix(xdal), s= "lambda.1se")
getErrs(pred, ydal)




print("Denver")
fit = cv.glmnet(data.matrix(xnotden), data.matrix(ynotden), alpha=1)
coef(fit, s="lambda.1se")

print(fit$lambda.1se)
pred = predict(fit, data.matrix(xden), s= "lambda.1se")
getErrs(pred, yden)



