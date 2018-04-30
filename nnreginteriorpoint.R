### generalpurpose routine
### arguments
### X --- inputs 
### y --- output
### objective --- objective function (X, y, beta) --- beta parameter vector
### gradient --- gradient of objective
### Hess --- Hessian of objective
### onlypositve --- TRUE [only if ell1 = TRUE] should we take nonnegative inputs only.
### regamount --- only of ell_1 = TRUE: regularization parameter
### should constant term be included (unregularized) ?
### solutionpath --- only if ell_1 = TRUE: approximation of the solution path on a grid
### cholmod --- default: FALSE; only for sparse matrices (-> format of X)
### eps --- numerical zero (used for all numerical tolerance computations)
### beta0 --- starting value for weight vector
### ... --- further arguments to be passed to the solution path computation routine.

nnreginteriorpoint <- function(X, y, objective, gradient, Hessian, onlypositive = TRUE,
                               regamount = 0,
                               solutionpath = FALSE,
                               offset = FALSE,
                               beta0 = NULL,
                               lambda0 = NULL, 
                               eps = 1e-6,
                               cholmod = FALSE,
                               functionarguments = list(),
                               solutionpatharguments = list(regmax = NULL, gridlength = 100, fac = 0.001, verbose = TRUE),
                               trace = TRUE){
  require(Matrix)
  ###
  if(!onlypositive)
    X <- cbind2(X, -X) ### expand feature set
  ###
  p <- ncol(X)
  n <- length(y)
  if(n != nrow(X)) stop("Input incorrect: number of rows of X do not match length(y) \n")
  namobj <- names(formals(objective))
  namgrad <- names(formals(gradient))
  namHess <- names(formals(Hessian))
  if(!identical(namobj[1:3], c("X", "y", "beta")) | !identical(namgrad[1:3], c("X", "y", "beta")) | !identical(namHess[1:3], c("X", "y", "beta")))
     stop("Invalid specification of objective, gradient or Hessian \n")

  if(is.null(beta0)){
       beta0 <- drop(t(X) %*% y)
       beta0[beta0 < 0] <- eps 
   }
     
  if(!is.null(beta0)){
    if(length(beta0) != p) stop("Length of 'beta0' does not match dimension of 'X' \n")
    if(!all(beta0  > 0))
     stop("Initial solution 'beta0' not strictly feasible \n")
  }
    
  if(is.null(lambda0))   
     lambda0 <- 1/beta0
     
  if(!is.null(lambda0))
    if(!all(lambda0  > 0))
     stop("Initial solution 'lambda0' not feasible \n")
   beta <- beta0
   lambda <- lambda0 

  eta <- sum(beta * lambda) ### 'surrogate' duality gap
  callist <- vector(mode = "list", length = 3)
  names(callist) <- c("X", "y", "beta")   
  if(length(functionarguments) > 0){
    callist <- c(callist, functionarguments)
  }
  ####   
  convergence <- FALSE
  ### fix some constants
  mu <- 10
  sigma <- 0.95
  kappa <- 0.01   
  ###   
  if(solutionpath){
    updatestart <- solutionpatharguments$updatestart
    if(is.null(updatestart)) updatestart <- TRUE
    ###
    gridpoints <- solutionpatharguments$gridpoints
    if(is.null(gridpoints)) gridpoints <- 100
    fac <- solutionpatharguments$fac
    if(is.null(fac)) fac <- 0.001
    verbose <- solutionpatharguments$verbose
    if(is.null(verbose)) verbose <- TRUE
    ### try to determine a suitable entry point
    callist$X <- X
    callist$y <- y
    callist$beta <- rep(eps, ncol(X))
    regmax <- solutionpatharguments$regmax
    if(is.null(regmax)){
      regmax <- max(abs(do.call("gradient", args = callist))) * 0.99
      if(!is.finite(regmax)){
       regmax <- max(drop(t(X) %*% y)) * 0.99
     }
    }  
    regmax <- abs(regmax)
   ### fix the grid
   log.reggrid.upper <- log(regmax)
   log.reggrid.lower <- log(fac) + log(regmax)
   log.reggrid <- seq(from = log.reggrid.lower, to = log.reggrid.upper, length = gridpoints - 1)
   reggrid <- c(rev(exp(log.reggrid)), eps)
   ### fix a matrix for storing coefficients 
   Beta <- matrix(nrow = ncol(X), ncol = gridpoints)
   if(offset) Offset <- numeric(gridpoints)
   else Offset <- NULL
   ### vector of starting values (to be updated --> warm starts)
   betastart <- beta0
   if(is.null(betastart)) dualstart <- NULL
   else  dualstart <- 1/betastart
   ### evaluate path
   for(j in seq(along = reggrid)){
      regj <- reggrid[j]
     if(verbose){
       cat("iteration:", j, "out of", gridpoints, "\t")
       cat("Value of regularization parameter:", regj, "\n")
     }
     resj <- nnreginteriorpoint(X = X, y = y, objective = objective, gradient = gradient, Hessian = Hessian,
                                onlypositive = TRUE,
                               regamount = regj,
                               solutionpath = FALSE,
                               offset = offset,
                               beta0 = betastart,
                               lambda0 = dualstart, 
                               eps = eps,
                               cholmod = cholmod,
                               functionarguments = functionarguments,
                               solutionpatharguments = list(),
                               trace = trace)  
      Beta[,j] <- resj$beta
      if(offset) Offset[j] <- resj$offset
      if(updatestart){
       betastart <- resj$beta
       betastart[betastart < eps] <- eps
       dualstart <- resj$lambda
       dualstart[dualstart < eps] <- eps
     }
    }
    if(!onlypositive)
      Betaprocessed <- Beta[1:(p/2),] - Beta[((p/2)+1):p,]
    else
      Betaprocessed <- NULL
    return(list(reggrid = reggrid, Offset = Offset, Beta = Beta,
               Betaprocessed = Betaprocessed))
  }
  
  
  
  if(!offset){
    callist$X <- X
    callist$y <- y 
  while(!convergence){
     gamma <- (p * mu)/eta
     callist$beta <- beta
     rdual <- drop(do.call("gradient", args = callist))  - lambda + regamount ### regamount can be 0.
     rcent <- lambda * beta - 1/gamma
     normold<- sqrt(sum(c(rdual^2, rcent^2)))
     ### 
     Hess <- do.call("Hessian", args = callist)   
     ### obtain updates for primal variables first
     diag(Hess) <- diag(Hess) + lambda/beta
     ###
     rhs.beta <- drop(-rcent/beta  - rdual)
     ###
     if(cholmod){
       Hess <- as(forceSymmetric(Hess), "sparseMatrix")
       R <- Cholesky(Hess)
       delta.beta <- drop(solve(R, rhs.beta))
     }
     else{
       DD <- diag(1/diag(Hess))
       Hess <- Hess %*% DD
       delta.beta <- drop(solve(Hess, rhs.beta)) * diag(DD)
     }
     ### obtain updates for dual variables
     delta.lambda <- (-rcent - lambda * delta.beta)/beta
     ###
     ### line search 
     finished <- FALSE
     stepsize <- (-lambda / delta.lambda) ### compute maximum stepsize
     if(length(stepsize[stepsize > 0]) > 0)  stepsize <- 0.99 * min(stepsize[stepsize > 0])
     else stepsize <- 0.99
     while(!all(beta + stepsize * delta.beta > 0))
       stepsize <- stepsize * sigma 
     while(!finished){
       if(trace) cat("linesearch...", stepsize, "\n")
       betatilde <- beta + stepsize * delta.beta
       callist$beta <- betatilde
       rdual <-  drop(do.call("gradient", args = callist) - (lambda + stepsize * delta.lambda) + regamount)
       rcent <-  (lambda + stepsize * delta.lambda)*betatilde - 1/gamma
       normnew <- sqrt(sum(c(rdual^2, rcent^2)))
       if(normnew < (1 - kappa * stepsize) * normold) finished <- TRUE
       else stepsize <- stepsize * sigma
       if(stepsize < (0.5 * .Machine$double.eps)){
       stop("Canceled stepsize selection. \n")
     }
    }
     ### end of line search
     ### check convergence and update
     beta <- betatilde
     lambda <- lambda + stepsize * delta.lambda
     ### update (surrogate) duality gap
     eta <- sum(beta * lambda)
     if(trace) cat("Duality gap: ", eta, "\t")
     norm.dual <- sqrt(sum(rdual^2))
     if(trace) cat("norm.dual:", norm.dual, "\t")
     if(norm.dual < eps & eta < eps) convergence <- TRUE
     objective <-  do.call("objective", args = callist) + regamount * sum(beta) ### negative pen. log-likelihood
     if(trace) cat("objective:", objective, "\n")
   }
  }  
  
  
  
  
  
  
    if(offset){
      callist$X <- cbind2(1, X)
    callist$y <- y
    beta <- c(eps, beta)
  while(!convergence){
     gamma <- (p * mu)/eta
     callist$beta <- beta
     rdual <- drop(do.call("gradient", args = callist))  - c(0,lambda) + c(0, rep(regamount, p)) ### regamount can be 0.
     rcent <- lambda * beta[-1] - 1/gamma
     normold<- sqrt(sum(c(rdual^2, rcent^2)))
     ### 
     Hess <- do.call("Hessian", args = callist)   
     ### obtain updates for primal variables first
     diag(Hess) <- diag(Hess) + c(0, lambda/beta[-1])
     ###
     rhs.beta <- drop(-c(0, rcent)/beta  - rdual)
     ###
     if(cholmod){
       Hess <- as(forceSymmetric(Hess), "sparseMatrix")
       R <- Cholesky(Hess)
       delta.beta <- drop(solve(R, rhs.beta))
     }
     else{
       DD <- diag(1/diag(Hess))
       Hess <- Hess %*% DD
       delta.beta <- drop(solve(Hess, rhs.beta)) * diag(DD)
       #delta.beta <- drop(solve(Hess, rhs.beta))
     }
     ### obtain updates for dual variables
     delta.lambda <- (-rcent - lambda * delta.beta[-1])/beta[-1]
     ###
     ### line search 
     finished <- FALSE
     stepsize <- (-lambda / delta.lambda) ### compute maximum stepsize
     if(length(stepsize[stepsize > 0]) > 0)  stepsize <- 0.99 * min(stepsize[stepsize > 0])
     else stepsize <- 0.99
     while(!all(beta[-1] + stepsize * delta.beta[-1] > 0))
       stepsize <- stepsize * sigma 
     while(!finished){
       if(trace) cat("linesearch...", stepsize, "\n")
       betatilde <- beta + stepsize * delta.beta
       callist$beta <- betatilde
       rdual <-  drop(do.call("gradient", args = callist)) - c(0, (lambda + stepsize * delta.lambda)) + c(0, rep(regamount, p))
       rcent <-  (lambda + stepsize * delta.lambda)*betatilde[-1] - 1/gamma
       normnew <- sqrt(sum(c(rdual^2, rcent^2)))
       if(normnew < (1 - kappa * stepsize) * normold) finished <- TRUE
       else stepsize <- stepsize * sigma
       if(stepsize < (0.5 * .Machine$double.eps)){
       stop("Canceled stepsize selection. \n")
     }
    }
     ### end of line search
     ### check convergence and update
     beta <- betatilde
     lambda <- lambda + stepsize * delta.lambda
     ### update (surrogate) duality gap
     eta <- sum(beta[-1] * lambda)
     if(trace) cat("Duality gap: ", eta, "\t")
     norm.dual <- sqrt(sum(rdual^2))
     if(trace) cat("norm.dual:", norm.dual, "\t")
     if(norm.dual < eps & eta < eps) convergence <- TRUE
     objective <- do.call("objective", args = callist) + regamount * sum(beta[-1]) ### negative pen. log-likelihood
     if(trace) cat("objective:", objective, "\n")
   }
  }  
    
  # 'postprocessing'
    if(offset){
      offset <- beta[1]
      beta <- beta[-1]
      if(!onlypositive)
      betaprocessed <- beta[1:((p/2))] - beta[((p/2) + 1):p]
      else
      betaprocessed <- NULL
    }  
    else{
      offset <- NULL
      if(!onlypositive)
      betaprocessed <- beta[1:(p/2)] - beta[((p/2) + 1):p]
      else
      betaprocessed <- NULL
    }
    
    
  # 'return'  
  return(list(beta = beta,
               betaprocessed = betaprocessed,
               offset = offset,
               lambda = lambda,
               dualitygap = eta,
               regamount = regamount,
               objective = objective))   
     
  }




    
