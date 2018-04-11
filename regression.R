


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

notbos = rbind(bosdata, chidata, ladata, atldata, daldata, dendata)
notchi = rbind(bosdata, chidata, ladata, atldata, daldata, dendata)
notla = rbind(bosdata, chidata, ladata, atldata, daldata, dendata)
notatl = rbind(bosdata, chidata, ladata, atldata, daldata, dendata)
notdal = rbind(bosdata, chidata, ladata, atldata, daldata, dendata)
notden = rbind(bosdata, chidata, ladata, atldata, daldata, dendata)

#print(colnames(alldata))

mod <- lm(ridership ~ near_employment + near_population, data=notbos)
pred <- predict(mod, bosdata)
print(pred - bosride$ridership)
#print(bosride$ridership)


