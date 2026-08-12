# P5 figure: TableShift-class Folktables/ACS generalization (leave-states-out).
# All numbers from p4_tableshift_result.json -- no hardcoded values.
# Paper float is A|B only: body cites Fig. f5 A/B; C/D are not cited, so they
# are not drawn. Makefile: `make figures`. Also sourced from p4_figs_expansions.R.
cargs <- commandArgs(trailingOnly = FALSE)
SDIR  <- dirname(normalizePath(sub("^--file=", "", cargs[grep("^--file=", cargs)][1])))
source(Sys.getenv("GGTHEME_R", file.path(SDIR, "ggtheme.R")))
library(patchwork)
ROOT <- Sys.getenv("ND1_RESULTS_ROOT",
        normalizePath(file.path(SDIR, "..", "..", "experiments", "results")))
TS   <- read_result(file.path(ROOT, "p4_tableshift_result.json"))

num <- function(x) if (is.null(x)) NA_real_ else suppressWarnings(as.numeric(x))
g   <- function(r, k) if (!is.null(r[[k]])) r[[k]] else NA

GBM_COLOURS <- c(LightGBM = okabe_ito[1], XGBoost = okabe_ito[2])

df <- do.call(rbind, lapply(TS$results, function(r) {
  if (!is.null(r$status) && r$status != "ok") return(NULL)
  data.frame(
    task_lab   = pretty_acs(g(r, "task")),
    model      = pretty_model(g(r, "model")),
    repair_ood = num(g(r, "repair_ood_med")),
    repair_lo  = num(g(r, "repair_ood_ci")[[1]]),
    repair_hi  = num(g(r, "repair_ood_ci")[[2]]),
    sub_gap    = num(g(r, "grouped_coverage_gap_worst_minus_best")),
    sub_gap_lo = num(g(r, "grouped_coverage_gap_ci")[[1]]),
    sub_gap_hi = num(g(r, "grouped_coverage_gap_ci")[[2]]),
    stringsAsFactors = FALSE)
}))
df$model <- factor(df$model, levels = c("LightGBM", "XGBoost"))
# Shared y-order (median OOD repair) so A and B are row-aligned.
task_ord <- names(sort(tapply(df$repair_ood, df$task_lab, median)))
df$task_lab <- factor(df$task_lab, levels = task_ord)
write.csv(df, file.path(SDIR, "p5_tableshift_table.csv"), row.names = FALSE)

# Native width ~ KBS preprint \linewidth so includegraphics[width=\linewidth]
# does not shrink 11 pt type. Tight margins: spines/data fill the canvas.
W_F5 <- 5.42
H_F5 <- 3.45
fill_theme <- theme(
  plot.margin        = margin(t = 10, r = 10, b = 8, l = 2),
  legend.position    = "bottom",
  legend.box.spacing = unit(1, "pt"),
  legend.margin      = margin(0, 0, 0, 0),
  plot.tag.position  = c(0.02, 1.06),
  axis.title.x       = element_text(margin = margin(t = 4))
)

pA <- ggplot(df, aes(task_lab, repair_ood, colour = model)) +
  geom_hline(yintercept = 0, linetype = 2, colour = "grey60") +
  geom_pointrange(aes(ymin = repair_lo, ymax = repair_hi),
                  position = position_dodge(0.45), size = 0.45, linewidth = 0.45) +
  scale_y_continuous(expand = expansion(mult = c(0.04, 0.06))) +
  scale_x_discrete(expand = expansion(add = 0.45)) +
  coord_flip() +
  scale_colour_manual(values = GBM_COLOURS, drop = FALSE) +
  labs(x = NULL, y = "OOD repair ratio", colour = NULL) +
  theme_paper() + fill_theme

pB <- ggplot(df, aes(task_lab, sub_gap, colour = model)) +
  geom_hline(yintercept = 0, linetype = 2, colour = "grey60") +
  geom_pointrange(aes(ymin = sub_gap_lo, ymax = sub_gap_hi),
                  position = position_dodge(0.45), size = 0.45, linewidth = 0.45) +
  scale_y_continuous(expand = expansion(mult = c(0.04, 0.06))) +
  scale_x_discrete(expand = expansion(add = 0.45)) +
  coord_flip() +
  scale_colour_manual(values = GBM_COLOURS, drop = FALSE) +
  labs(x = NULL, y = "Coverage gap (worst − best)", colour = NULL) +
  theme_paper() + fill_theme

save_fig(pA, file.path(SDIR, "F5a_tableshift_repair"), w = W_F5 / 2, h = H_F5)
save_fig(pB, file.path(SDIR, "F5b_tableshift_subgroup_gap"), w = W_F5 / 2, h = H_F5)

f5 <- (pA | pB) +
  plot_layout(guides = "collect", widths = c(1, 1)) +
  plot_annotation(tag_levels = "A") &
  theme(
    plot.tag          = element_text(family = PAPER_FONT, face = "bold",
                                      size = 11, colour = "black"),
    plot.tag.position = c(0.02, 1.06),
    legend.position   = "bottom"
  )
save_fig(f5, file.path(SDIR, "F5_tableshift"), w = W_F5, h = H_F5)

cat(sprintf("P5 TableShift A|B done. n cells=%d  canvas=%.2fx%.2fin\n",
            nrow(df), W_F5, H_F5))
cat(sprintf("median repair XGB=%.5f LGBM=%.5f | median subgap XGB=%.4f LGBM=%.4f\n",
            num(TS$per_model_summary$xgboost$median_repair_ood),
            num(TS$per_model_summary$lightgbm$median_repair_ood),
            num(TS$per_model_summary$xgboost$median_grouped_coverage_gap),
            num(TS$per_model_summary$lightgbm$median_grouped_coverage_gap)))
