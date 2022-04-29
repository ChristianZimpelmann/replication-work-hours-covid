library(stringr)

nice_reg_table <- function(stargazer_object, labels, path){
  "
  stargazer_object (character vector)
  labels (list): variable labels
  path (character): where to save table, the best to save them where
                    the stargazer saved the uncleaned one

  "
  # Transform labels to account for stargazer
  trans_labels <- labels
  trans_label_names <- str_replace_all(names(labels), "_", "\\\\_")
  names(trans_labels) <- trans_label_names
  trans_labels <- unlist(trans_labels)

  # Additional replacements
  other_labels <- c(
    "(0.0)"="",
    "(0.00)"="",
    "(0.000)"="",
    ":"= " $\\times$ "
  )

  # Replace
  out <- gsub("([a-z_0-9\\\\]+):(March\\\\_April)", "\\2:\\1", stargazer_object)
  out <- gsub("([a-z_0-9\\\\]+):(May)", "\\2:\\1", out)
  out <- gsub("([a-z_0-9\\\\]+):(June)", "\\2:\\1", out)
  out <- gsub("([a-z_0-9\\\\]+):(September)", "\\2:\\1", out)
  out <- gsub("([a-z_0-9\\\\]+):(December)", "\\2:\\1", out)
  out <- str_replace_all(out, pattern=fixed(other_labels))
  out <- str_replace_all(out, pattern=fixed(trans_labels))
  out <- gsub("(\\(|\\[)([0-9]+), ([0-9]+)(\\)|\\])", " \\2-\\3", out)
  out <- gsub("Dependent variable $\\times$", "Dependent variable:", out,fixed = TRUE)

  # Write to file
  out <- paste(out, collapse="\n")
  fileConn <- file(path)
  writeLines(out, fileConn)
  close(fileConn)

}

basic_formula_gender_hours <- function(outcome, additional_variables, fe=0){
  "

    outcome (character)
    additional_variables (character vector)
    fe (character)

  "

  add <- paste0(
      "+ (", paste(additional_variables, collapse=" + "), ") * (March_April + May + June + September + December)"
    )

  formula <- as.formula(paste0(
      outcome, "~",
      "March_April + May + June + September + December",
      "+ female + March_April:female + May:female +  June:female + September:female + December:female",
      add,
      "|", fe,
      "| 0 | hh_id"
  ))

  return(formula)
}
