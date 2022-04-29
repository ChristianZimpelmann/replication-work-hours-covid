"

Quantile Regression HH income

"
library(arrow)
library(lfe)
library(broom)
library(tidyverse)
library(dplyr)
library(lubridate)
library(stargazer)
library(quantreg)
library(data.table)
library(xtable)
source("project_paths.r")
source(paste(PATH_LIBRARY, "reg_table_functions.r", sep="/"))


# Load data
data <- read_parquet(
  paste(PATH_OUT_DATA, "work-childcare-long.parquet", sep="/")
)

df <- data %>% filter(age >= 18 & age <= 66 & year(month) != 2019)
hh_income <- read_parquet(
  paste(PATH_OUT_DATA, "hh_income.parquet", sep="/")
)

to_merge <- hh_income %>% select(
	"net_income_hh_equiv", "rel_change_net_income_hh_equiv",
	"month", "personal_id"
)

df <- merge(df, to_merge, by=c("month", "personal_id"))

df["month_num"] = month(df$month)

# Subselect employed
work_data <- df %>% filter(
  !(rel_change_net_income_hh_equiv %>% is.na())
  & !(self_employed_baseline %>% is.na())
  & !(rel_change_hours_uncond %>% is.na())
  & (work_status_baseline %in% c("employed", "self-employed"))
  & max_hours_total >= 10
  & !(month(month) %in% c(1,2,3))
)

# Redefine relative changes
work_data$rel_change_net_income_hh_equiv <- work_data$rel_change_net_income_hh_equiv*100
work_data$rel_change_hours <- work_data$rel_change_hours*100

# Define Status Variables
# Variables should define unique paths through extensive margin employment
work_data["lost_job"] <- 0
work_data$lost_job[(
  (work_data$work_status %in% c("unemployed"))
)] <- 1
work_data$lost_job[work_data$work_status %>% is.na()] <- NA

work_data["transition_out"] <- 0
work_data$transition_out[(
  (work_data$work_status
  	%in% c("homemaker", "retired", "social assistance", "student or trainee"))
)] <- 1
work_data$transition_out[work_data$work_status %>% is.na()] <- NA

work_data["employed_baseline"] <- 1
work_data$employed_baseline[work_data$self_employed_baseline == 1] <- 0

work_data["self_employed"] <- 0
work_data$self_employed[(work_data$work_status == 'self-employed')] <- 1

work_data["employed"] <- 0
work_data$employed[(work_data$work_status == 'employed')] <- 1

work_data["trans_empl_self_empl"] <- 0
work_data$trans_empl_self_empl[
  (
    ((work_data$work_status_baseline %in% c("employed"))
    & (work_data$self_employed == 1))
    | ((work_data$work_status_baseline %in% c("self-employed"))
    & (work_data$employed == 1))
  )
] <- 1
work_data$employed[(work_data$trans_empl_self_empl == 1)] <- 0
work_data$self_employed[(work_data$trans_empl_self_empl == 1)] <- 0


work_data["status"] <- NA
work_data$status[work_data$employed == 1] <- "employed"
work_data$status[work_data$self_employed == 1] <- "self-employed"
work_data$status[work_data$trans_empl_self_empl ==1] <- "transition btw employed/self-employed"
work_data$status[work_data$transition_out == 1] <- "dropped out of labor force"
work_data$status[work_data$lost_job == 1] <- "transition unemployed"


work_data["got_job"] <- 0
work_data$got_job[(
  !(work_data$work_status_baseline %in% c("employed", "self-employed"))
  & (work_data$work_status %in% c("employed", "self-employed"))
)] <- 1
work_data$got_job[work_data$work_status %>% is.na()] <- NA

# Table function
renaming_table <- function(out, kind){
	if(kind=="policy"){
		out$covariates <- sub("factor(month_num)4", "Apr", out$covariates, fixed = TRUE)
		out$covariates <- sub("factor(month_num)5", "May", out$covariates, fixed = TRUE)
		out$covariates <- sub("factor(month_num)6", "Jun", out$covariates, fixed = TRUE)
		out$covariates <- sub("factor(month_num)9", "Sep", out$covariates, fixed = TRUE)
		out$covariates <- sub(
			"employed:know",
			"Policy: I don't know $\\times$ employed (pre-Covid) $\\Rightarrow$ employed",
			out$covariates, fixed = TRUE
		)
		out$covariates <- sub(
			"yes:employed",
			"Policy: Yes $\\times$ employed (pre-Covid) $\\Rightarrow$ employed",
			out$covariates, fixed = TRUE
		)
		out$covariates <- sub(
			"yes:self_employed",
			"Policy: Yes $\\times$ self-empl (pre-Covid) $\\Rightarrow$ self-empl",
			out$covariates, fixed = TRUE
		)
		out$covariates <- sub(
			"self_employed",
			"self-empl (pre-Covid) $\\Rightarrow$ self-empl",
			out$covariates, fixed = TRUE
			)
		out$covariates <- sub("lost_job", "empl or self-empl (pre-Covid) $\\Rightarrow$ unemployed", out$covariates, fixed = TRUE)
		out$covariates <- sub("transition_out", "empl or self-empl (pre-Covid) $\\Rightarrow$ out of labor force", out$covariates, fixed = TRUE)
		ordered <- c(
		  "Policy: Yes $\\times$ employed (pre-Covid) $\\Rightarrow$ employed",
		  "Policy: I don't know $\\times$ employed (pre-Covid) $\\Rightarrow$ employed",
		  "Policy: Yes $\\times$ self-empl (pre-Covid) $\\Rightarrow$ self-empl",
		  "self-empl (pre-Covid) $\\Rightarrow$ self-empl",
		  "empl or self-empl (pre-Covid) $\\Rightarrow$ unemployed",
		  "empl or self-empl (pre-Covid) $\\Rightarrow$ out of labor force",
		  "Apr", "May", "Jun", "Sep"
		)
		out <- out %>% arrange(factor(covariates, levels = ordered))
	} else {
		out$covariates <- sub("factor(month_num)", "", out$covariates, fixed = TRUE)
		out$covariates <- sub("rel_change_hours_uncond", "rel. change in work. hours", out$covariates, fixed = TRUE)
		out$covariates <- sub("self_employed", "self-empl (pre-Covid)/self-empl", out$covariates, fixed = TRUE)
		out$covariates <- sub("employed", "employed (pre-Covid)/employed", out$covariates, fixed = TRUE)
		out$covariates <- sub("lost_job", "empl or self-empl (pre-Covid)/unemployed", out$covariates, fixed = TRUE)
		out$covariates <- sub("transition_out", "empl or self-empl (pre-Covid)/out of labor force", out$covariates, fixed = TRUE)
		out$covariates <- sub("trans_empl_self_empl", "transition empl/self-empl", out$covariates, fixed = TRUE)
		out$covariates <- sub("got_job", "transitioned to employed", out$covariates, fixed = TRUE)
		out$covariates <- sub("hhh_partnerTRUE", "lives with partner", out$covariates, fixed = TRUE)
		out$covariates <- sub(":", " $\\times$ ", out$covariates, fixed = TRUE)
		old <- c("4","5","6","9")
		new <- c("April", "May", "June", "September")
		out$covariates[out$covariates %in% old] <- new[match(out$covariates,old, nomatch=0)]
		ordered <- c(
		  "rel. change in work. hours $\\times$ employed (pre-Covid)/employed",
		  "rel. change in work. hours $\\times$ self-empl (pre-Covid)/self-empl",
		  "self-empl (pre-Covid)/self-empl",
		  "empl or self-empl (pre-Covid)/unemployed",
		  "empl or self-empl (pre-Covid)/out of labor force",
		  "April", "May", "June", "September"
		)
		out <- out %>% arrange(factor(covariates, levels = ordered))
	}
	return(out)

}
latex_table <- function(s, path, kind="main"){
	"
		s = rq summary object
	"
	# Make Nice Data Frame
	df_list <- list()
	i <- 1
	for(p in c("p25", "p50", "p75")){
	  d <- as.data.frame(s[[i]]$coefficients)
	  d <- d %>% select("Value", "Std. Error", "Pr(>|t|)")
	  colnames(d) <- c(p, paste0(p, "_se"), paste0(p, "_pvalue"))
	  df_list[[p]] <- d
	  i <- i + 1
	}

	out <- bind_cols(df_list)
	out["covariates"] <- rownames(out)
	if(kind=='policy'){
	  out <- out %>% filter(covariates != "policy_dummyI don't know:self_employed")
	 }
	out <- renaming_table(out, kind=kind)
	rownames(out) <- out$covariates
	out <- out %>% select(-covariates)

	# Transform data frame to row coef (se)
	col_list <- list()
	for(p in c("p25", "p50", "p75")){
	  se <- paste0("(", round(out[[paste0(p, "_se")]], 2), ")")
	  pvalue <- out[paste0(p, "_pvalue")]
	  out["star"] <- ""
	  out[pvalue < 0.1, "star"] <- "$^{*}$"
	  out[pvalue < 0.05, "star"] <- "$^{**}$"
	  out[pvalue < 0.01, "star"] <- "$^{***}$"
	  coef <- paste0(as.character(round(out[[p]], 2)) , out$star)

	  coef_list <- list()
	  for(i in 1:length(coef)){
	    c <- data.frame(coef[i])
	    rownames(c) <- rownames(out)[i]
	    colnames(c) <- p
	    see <- data.frame(se[i])
	    colnames(see) <- p
	    cs <- rbind(c, see)
	    coef_list[[i]] <- cs
	  }

	  col <- bind_rows(coef_list)
	  col_list[[p]] <- col

	}

	clean_rownames <- function(x){
	  out <- x
	  if(startsWith(x, "1")){
	    out <- ""
	  }
	  return(out)
	}

	tab <- bind_cols(col_list)
	tab$covariates <- as.vector(sapply(rownames(tab), FUN=clean_rownames, simplify=TRUE))
	tab <- tab %>% select(covariates, p25, p50, p75)

	header1 <- data_frame(a="", b="\\multicolumn{3}{c}{Rel. change net equiv. HH inc. (\\%)}\\\\ \\cmidrule{2-4} \\addlinespace %", c="", d="")
	colnames(header1) <- colnames(tab)
	header2 <- data_frame("","p25", "p50", "p75 \\\\ \\midrule %")
	colnames(header2) <- colnames(tab)

	library(data.table)
	foot1 <- transpose(data.frame("bli"=c("\\midrule \\addlinespace%", rep("", 3))))
	foot2 <- transpose(data.frame("bla"=c("N", rep(dim(work_data)[1], 3))))
	foot <- rbind(foot1, foot2)
	colnames(foot) <- colnames(tab)

	final <- bind_rows(header1, header2, tab, foot)

	# Export to latex
	print(
	  xtable(final),
	  file=path,
	  type='latex',
	  sanitize.text.function=identity,
	  include.rownames=FALSE,
	  include.colnames=FALSE,
	  floating=FALSE,
	  booktabs=TRUE
	)

}

# Create regresssions main regression
rqfit <- rq(
  rel_change_net_income_hh_equiv ~ rel_change_hours_uncond:employed
  + rel_change_hours_uncond:self_employed
  + self_employed + lost_job + transition_out
  + factor(month_num) - 1,
  data=work_data %>% filter(trans_empl_self_empl == 0), tau=c(0.25, 0.50, 0.75), method="sfn"
)

# Calculate different summary
s_iid <- summary(rqfit, se="nid")
s_boot <- summary(rqfit, se="boot", bsmethod="cluster", R=200, cluster=(work_data %>% filter(trans_empl_self_empl == 0))$hh_id)


# Make tables
path = paste(
	PATH_OUT_TABLES,
	"hh_income",
	"quantile_regression_income_iid.tex",
	sep="/"
)
latex_table(s_iid, path)

path = paste(
	PATH_OUT_TABLES,
	"hh_income",
	"quantile_regression_income_boot.tex",
	sep="/"
)
latex_table(s_boot, path)

# Create policy regression regression
work_data["policy_dummy"] = work_data["applied_any_policy_cat_05"]
work_data$policy_dummy[month(work_data$month) %in% c(6, 7, 8, 9)] = (
  work_data$applied_any_policy_cat_09[month(work_data$month) %in% c(6, 7, 8, 9)]
)
work_data$policy_dummy <- factor(work_data$policy_dummy, order=FALSE)

work_data$policy_dummy[work_data$transition_out == 1] = 'no'
work_data$policy_dummy[work_data$lost_job == 1] = 'no'

policy_data <- work_data %>% filter(
  #(work_data$work_status %in% c("employed", "self-employed"))
  trans_empl_self_empl == 0
  & month(month) <= 9
  & ! (
    work_data$self_employed == 1
    & work_data$policy_dummy == "I don't know"
  ) & !(policy_dummy %>% is.na())
)

policy_data["yes"] <- (policy_data$policy_dummy == 'yes')*1
policy_data["no"] <- (policy_data$policy_dummy == 'no')*1
policy_data["know"] <- (policy_data$policy_dummy == "I don't know")*1
rqfit <- rq(
  rel_change_net_income_hh_equiv ~ yes:employed + know:employed
  + yes:self_employed + self_employed + transition_out + lost_job
  + factor(month_num) - 1,
  data=policy_data, tau=c(0.25, 0.50, 0.75), method="sfn"
)

# Calculate different summary
s_iid <- summary(rqfit, se="nid")
s_boot <- summary(
  rqfit, se="boot", bsmethod="cluster", R=200,
  cluster=(policy_data)$hh_id
)


# Make tables
path = paste(
  PATH_OUT_TABLES,
  "hh_income",
  "quantile_regression_income_policy_iid.tex",
  sep="/"
)
latex_table(s_iid, path, kind="policy")

path = paste(
  PATH_OUT_TABLES,
  "hh_income",
  "quantile_regression_income_policy_boot.tex",
  sep="/"
)
latex_table(s_boot, path, kind="policy")



