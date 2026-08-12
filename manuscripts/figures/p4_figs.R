# P4 structured-data — statistical figures from the REAL result JSONs (verified key paths, no reshape2).
# reliability-commons paper-template pattern: reads ONLY on-disk result JSONs,
# writes PDF+PNG (via save_fig/ggsave) into this figures/ dir.
# Run: `make figures` from manuscripts/, or Rscript from any cwd.
cargs <- commandArgs(trailingOnly = FALSE)
SDIR  <- dirname(normalizePath(sub("^--file=", "", cargs[grep("^--file=", cargs)][1])))
source(Sys.getenv("GGTHEME_R", file.path(SDIR, "ggtheme.R")))
library(patchwork)
ROOT <- Sys.getenv("ND1_RESULTS_ROOT",
        normalizePath(file.path(SDIR, "..", "..", "experiments", "results")))
S2   <- read_result(file.path(ROOT, "nd1_s2_lightgbm_mondrian.json"))
# Calibration-size diagnostic: reconciled RNG, key-included (SUCCESS) and
# key-excluded (KILL) twins -- F4 shows both to disclose the key-dependence.
DIA_KI <- read_result(file.path(ROOT, "nd1_s2_p4_calsize_diag_reconciled.json"))
DIA_KE <- read_result(file.path(ROOT, "nd1_s2_p4_calsize_diag_reconciled_keyexcluded.json"))
# FM arms (all read on the 14 keyed datasets): TabICLv2 leakage-ablated,
# n_estimators=16, de-staled GBM reference; and TabDPT, the second FM.
FM   <- read_result(file.path(ROOT, "nd1_tabicl_fm_arm_leakage_ablation.json"))
DPT  <- read_result(file.path(ROOT, "nd1_tabdpt_fm_arm.json"))
AGG  <- read_result(file.path(ROOT, "split_repeats", "aggregate-split-repeats-2026-07-02.json"))
# The 14 datasets carrying a defensible entity/time key (the paper's headline
# suite); the FM arms also run 16 extra arbitrary-key datasets we exclude here.
KEYED14 <- c("electricity","eucalyptus","adult","cylinder-bands","churn","Moneyball",
             "kick","black_friday","house_prices_nominal","colleges",
             "Airlines_DepDelay_10M","nyc-taxi-green-dec-2016","house_sales",
             "sf-police-incidents")
num  <- function(x) if (is.null(x)) NA_real_ else suppressWarnings(as.numeric(x))
g    <- function(r, k) if (!is.null(r[[k]])) r[[k]] else NA

df <- do.call(rbind, lapply(S2$results, function(r) data.frame(
  model          = as.character(g(r, "model")),
  name           = as.character(g(r, "name")),
  aurc_random    = num(g(r, "aurc_random")),
  aurc_grouped   = num(g(r, "aurc_grouped")),
  repair_grouped = num(g(r, "repair_ratio_grouped")),
  cov_grouped    = num(g(r, "conformal_cov_grouped_split")),
  stringsAsFactors = FALSE)))
df <- df[!is.na(df$aurc_random) & !is.na(df$aurc_grouped), ]
write.csv(df, file.path(SDIR, "p4_table.csv"), row.names = FALSE)

# F1: AURC random vs grouped per dataset, faceted by model (base-R long form).
# Per-dataset AURC spans classification tasks (~0.02) to regression tasks
# (~5.8e4) -- six orders of magnitude -- so a shared LINEAR axis collapses every
# classification dataset to an invisible zero-width sliver while a couple of
# regression datasets dominate the frame (the flagged mixed-scale-axis issue).
# Fix: a log10 AURC axis with paired points (a dumbbell per dataset) instead of
# bars. Bars carry a meaningless baseline on a log axis; the dumbbell keeps every
# dataset legible AND reads the random->grouped shift directly (grouped sits to
# the right = higher AURC = degraded). No plotted value is transformed.
m1 <- rbind(
  data.frame(model = df$model, name = df$name, split = "random",       aurc = df$aurc_random),
  data.frame(model = df$model, name = df$name, split = "grouped/time", aurc = df$aurc_grouped))
m1$split <- factor(m1$split, levels = c("random", "grouped/time"))
f1 <- ggplot(m1, aes(aurc, reorder(name, aurc))) +
  geom_line(aes(group = interaction(model, name)), colour = "grey70", linewidth = 0.4) +
  geom_point(aes(colour = split), size = 2) +
  facet_wrap(~model) + scale_color_paper() +
  scale_x_log10() +
  labs(x = "risk-coverage AURC (log scale; lower=better)", y = NULL, colour = "split") +
  theme_paper()
# F1/F2 4-panel assets come from p4_figs_expansions.R; do not overwrite.
# save_fig(f1, file.path(SDIR, "F1_aurc_random_vs_grouped"), w = 5.7, h = 3.56)

# F2: grouped repair ratio per dataset (fraction of random-deferral AURC removed; >0 = improves)
f2 <- ggplot(df, aes(reorder(name, repair_grouped), repair_grouped, colour = model)) +
  geom_hline(yintercept = 0, linetype = 2, colour = "grey60") +
  geom_point(size = 2.5) + coord_flip() + scale_color_paper() +
  labs(x = NULL, y = "grouped repair ratio\n(share of random-deferral AURC removed)") + theme_paper()
# save_fig(f2, file.path(SDIR, "F2_repair_ratio"), w = 4.36, h = 3.35)

# F3: model-agnosticism — two panels
#   Panel A: XGB vs LGBM grouped AURC scatter (14 datasets)
xs <- df[df$model == "xgboost",  c("name", "aurc_grouped")]; names(xs)[2] <- "xgboost"
ls <- df[df$model == "lightgbm", c("name", "aurc_grouped")]; names(ls)[2] <- "lightgbm"
w  <- merge(xs, ls, by = "name")
pA <- ggplot(w, aes(xgboost, lightgbm)) +
  geom_abline(slope = 1, intercept = 0, linetype = 2, colour = "grey60") +
  geom_point(size = 2.5, colour = okabe_ito[1]) +
  labs(x = "grouped AURC — XGBoost", y = "grouped AURC — LightGBM") + theme_paper()

#   Panel B: grouped conformal coverage — all 3 model families on all 14 datasets
#   XGBoost and LightGBM values taken from S2 JSON; TabICLv2 from full-14 FM JSON.
gbm_cov <- do.call(rbind, lapply(S2$results, function(r) {
  cv <- num(g(r, "conformal_cov_grouped_split"))
  if (!is.na(cv)) {
    data.frame(model = as.character(g(r, "model")),
               name  = as.character(g(r, "name")),
               cov_grouped = cv,
               stringsAsFactors = FALSE)
  }
}))
fm_cov_from <- function(res, label) do.call(rbind, lapply(res, function(r) {
  if (!is.null(r[["status"]]) && r[["status"]] == "ok" &&
      as.character(g(r, "name")) %in% KEYED14) {
    data.frame(model       = label,
               name        = as.character(g(r, "name")),
               cov_grouped = num(g(r, "conformal_cov_grouped")),
               stringsAsFactors = FALSE)
  }
}))
fm_cov  <- fm_cov_from(FM$results,  "TabICLv2")
dpt_cov <- fm_cov_from(DPT$results, "TabDPT")
cov4 <- rbind(gbm_cov, fm_cov, dpt_cov)
# lightgbm/xgboost first, matching the factor order (and hence okabe_ito
# colour) that F2 and F5 use for the same two model arms -- level order here
# used to put xgboost first, which silently flipped which colour meant which
# model between figures.
cov4$model <- factor(cov4$model, levels = c("lightgbm", "xgboost", "TabICLv2", "TabDPT"))

pB <- ggplot(cov4, aes(reorder(name, cov_grouped), cov_grouped,
                        colour = model, shape = model)) +
  geom_hline(yintercept = 0.90, linetype = 2, colour = "grey50", linewidth = 0.5) +
  geom_point(size = 2.4, position = position_dodge(0.6)) +
  scale_color_paper() +
  scale_shape_manual(values = c(16, 17, 15, 18)) +
  scale_y_continuous(limits = c(0.15, 1.02), breaks = seq(0.2, 1.0, 0.1)) +
  coord_flip() +
  labs(x = NULL, y = "grouped conformal coverage (target 0.90)",
       colour = "model", shape = "model") +
  guides(colour = guide_legend(nrow = 2), shape = guide_legend(nrow = 2)) +
  theme_paper() + theme(legend.position = "bottom")

## Panel A is a plain scatter with short numeric axis text; panel B's row
## labels (dataset names, up to ~20 characters) are much wider. Composing
## them with `/` by default aligns every gutter column across the stack, so
## A's y-axis-title column gets stretched to match B's wide row-label
## gutter, stranding the title away from its own tick numbers (visible
## white gap). free(type="panel") exempts A's panel from that cross-panel
## alignment so its title stays flush to its own axis; B is unaffected.
f3 <- (free(pA, type = "panel") / pB) + plot_layout(heights = c(1, 1.6)) +
  plot_annotation(tag_levels = "A") &
  paper_tag_theme
save_fig(f3, file.path(SDIR, "F3_model_agnostic"), w = 5.5, h = 7.7)

# F4: calibration-size diagnostic (reconciled RNG) -- key-included vs key-excluded.
#   Panel A (key-included) PASSES the preregistered bar (mechanism established);
#   Panel B (key-excluded) collapses to no relationship (KILL) -- the mechanism is
#   itself key-dependent. Both panels read the *_reconciled JSON's `rows` block.
#   Point colour is the same in both panels (no legend distinguishes it, so a
#   panel-specific hue would be decorative, not data-carrying); the panel
#   split alone conveys key-included vs key-excluded.
calsize_panel <- function(diag) {
  fr <- do.call(rbind, lapply(diag$rows, function(r) data.frame(
    cal  = num(g(r, "uncbin_cal_median")),
    mond = num(g(r, "mondrian_improvement_med")),
    stringsAsFactors = FALSE)))
  fr <- fr[is.finite(fr$cal) & is.finite(fr$mond), ]
  rho <- suppressWarnings(cor(fr$cal, fr$mond, method = "spearman"))
  p <- ggplot(fr, aes(cal, mond)) +
    geom_hline(yintercept = 0, linetype = 3, colour = "grey50") +
    geom_point(size = 2.5, colour = okabe_ito[4]) +
    geom_smooth(method = "lm", se = TRUE, colour = okabe_ito[1], linewidth = 0.6) +
    scale_x_log10() +
    labs(x = "per-bin calibration fold size (log)", y = "Mondrian coverage improvement") +
    theme_paper()
  list(plot = p, rho = rho, n = nrow(fr))
}
f4a <- calsize_panel(DIA_KI)
f4b <- calsize_panel(DIA_KE)
f4 <- (f4a$plot / f4b$plot) + plot_annotation(tag_levels = "A") &
  paper_tag_theme
save_fig(f4, file.path(SDIR, "F4_calsize_vs_mondrian"), w = 5, h = 6)

# F6: split-realization fragility -- distribution of ALL FOUR headline counts over
#   K repeated split draws (Stage-2, LightGBM, key-included). The same frozen node
#   carries four per-draw count distributions; showing all four makes the
#   realization-robustness picture direct: the grouped-gap and AURC-degrade counts
#   straddle the majority threshold (fragile), under-coverage sits below it (a
#   minority result), and repair-beats-random sits at the top and never drops below
#   it (robust). Reads the split-repeats aggregate JSON (no value recomputed).
mk_dist <- function(node, label) {
  vals <- as.integer(unlist(node$per_k, use.names = FALSE))
  data.frame(metric = label,
             k = seq_along(vals),
             count = vals,
             stringsAsFactors = FALSE)
}
s2ki <- AGG$stage2$key_included
frag <- rbind(
  mk_dist(s2ki$lightgbm$grouped_gap_count,   "grouped-gap count"),
  mk_dist(s2ki$lightgbm$aurc_degrade_count,  "AURC-degrade count"),
  mk_dist(s2ki$lightgbm$undercover_count,    "under-coverage count"),
  mk_dist(s2ki$lightgbm$repair_count,        "repair-beats-random count"))
frag$metric <- factor(frag$metric, levels = c(
  "grouped-gap count", "AURC-degrade count",
  "under-coverage count", "repair-beats-random count"))
frag <- frag[is.finite(frag$count) & frag$count > 0, ]
maj <- num(g(AGG, "majority_threshold"))
f6 <- ggplot(frag, aes(count, fill = metric)) +
  geom_hline(yintercept = 0, colour = "grey85") +
  geom_bar(position = position_dodge(preserve = "single"), width = 0.85) +
  geom_vline(xintercept = maj - 0.5, linetype = 2, colour = "grey40") +
  annotate("text", x = maj - 0.5, y = Inf, label = "majority = 8", hjust = 1.1,
           vjust = 1.5, size = 3.5, colour = "black", family = PAPER_FONT) +
  scale_fill_paper() +
  scale_x_continuous(breaks = 0:14) +
  labs(x = "count out of 14 datasets", y = "number of split draws",
       fill = NULL) +
  guides(fill = guide_legend(nrow = 2)) +
  theme_paper() + theme(legend.position = "bottom")
save_fig(f6, file.path(SDIR, "F6_split_repeats_fragility"), w = 5, h = 3.0)

cat("P4 figures done. n records=", nrow(df),
    " F4 rho_ki=", round(f4a$rho, 3), " (n=", f4a$n, ")",
    " rho_ke=", round(f4b$rho, 3), " (n=", f4b$n, ")\n")
cat("F3 panel B: n rows=", nrow(cov4), " (14 datasets x 4 model families)\n")
cat("F6: split draws per metric:",
    paste(levels(frag$metric), "=", tapply(frag$count, frag$metric, length),
          collapse = "  "), "\n")
