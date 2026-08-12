# p4_figs_expansions.R -- F1-F6 from frozen on-disk result JSONs (no hardcoded
# numeric values). Visual-QA pass: human-readable labels, tags in the margin,
# collected legends outside the data, no redundant A/B/C/D in panel titles.
cargs <- commandArgs(trailingOnly = FALSE)
SDIR  <- dirname(normalizePath(sub("^--file=", "", cargs[grep("^--file=", cargs)][1])))
source(Sys.getenv("GGTHEME_R", file.path(SDIR, "ggtheme.R")))
library(patchwork)
ROOT <- Sys.getenv("ND1_RESULTS_ROOT",
        normalizePath(file.path(SDIR, "..", "..", "experiments", "results")))

num  <- function(x) if (is.null(x)) NA_real_ else suppressWarnings(as.numeric(x))
g    <- function(r, k) if (!is.null(r[[k]])) r[[k]] else NA
vec  <- function(x) unlist(x, use.names = FALSE)
`%||%` <- function(a, b) if (!is.null(a)) a else b

KEYED14 <- c("electricity","eucalyptus","adult","cylinder-bands","churn","Moneyball",
             "kick","black_friday","house_prices_nominal","colleges",
             "Airlines_DepDelay_10M","nyc-taxi-green-dec-2016","house_sales",
             "sf-police-incidents")
MODEL_LEVS <- c("LightGBM", "XGBoost", "TabICLv2", "TabDPT")
SPLIT_LEVS <- c("random", "grouped")
SHAPE_VALS <- c(LightGBM = 16, XGBoost = 17, TabICLv2 = 15, TabDPT = 18)
COLOR_VALS <- setNames(okabe_ito[seq_along(MODEL_LEVS)], MODEL_LEVS)
MODEL_COLOURS <- COLOR_VALS
MODEL_SHAPES  <- SHAPE_VALS

# Native width matches the narrower venue textwidth (sn-jnl ~5.15 in) so
# includegraphics[width=\linewidth] does not shrink 8--11 pt figure type.
W <- 5.20
P4_ONLY <- Sys.getenv("P4_ONLY", Sys.getenv("ONLY_FIG", ""))
want_fig <- function(id) {
  P4_ONLY %in% c("", id, if (id %in% c("F1", "F2")) "F12")
}
crowded_y <- theme(axis.text.y = element_text(size = 8, colour = "black",
                                              lineheight = 0.92))
shared_legend <- theme(legend.position = "bottom",
                       legend.box = "horizontal",
                       legend.margin = margin(t = 0, r = 0, b = 0, l = 0))

# ---- data loading ------------------------------------------------------------
S2KI  <- read_result(file.path(ROOT, "nd1_s2_lightgbm_mondrian.json"))
S2KE  <- read_result(file.path(ROOT, "nd1_s2_lightgbm_mondrian_keyexcluded.json"))
FM    <- read_result(file.path(ROOT, "nd1_tabicl_fm_arm_leakage_ablation.json"))
FMKE  <- read_result(file.path(ROOT, "nd1_tabicl_fm_arm_leakage_ablation_keyexcluded.json"))
DPT   <- read_result(file.path(ROOT, "nd1_tabdpt_fm_arm.json"))
GBMB  <- read_result(file.path(ROOT, "nd1_tuned_gbm_baseline.json"))
DIAKI <- read_result(file.path(ROOT, "nd1_s2_p4_calsize_diag_reconciled.json"))
DIAKE <- read_result(file.path(ROOT, "nd1_s2_p4_calsize_diag_reconciled_keyexcluded.json"))
AGG   <- read_result(file.path(ROOT, "split_repeats", "aggregate-split-repeats-2026-07-02.json"))
TS    <- read_result(file.path(ROOT, "p4_tableshift_result.json"))
PLAN  <- read_result(normalizePath(file.path(SDIR, "..", "..",
           "experiments", "calsize_planning_2026-08-01", "results.json")))

arm_df <- function(res_json, label = NULL) {
  rows <- lapply(res_json$results, function(r) {
    if (!is.null(r$status) && r$status == "ok" &&
        (is.null(KEYED14) || as.character(g(r, "name")) %in% KEYED14)) {
      data.frame(
        model          = pretty_model(label %||% as.character(g(r, "model"))),
        name           = pretty_dataset(as.character(g(r, "name"))),
        aurc_random    = num(g(r, "aurc_random")),
        aurc_grouped   = num(g(r, "aurc_grouped")),
        repair_grouped = num(g(r, "repair_ratio_grouped")),
        cov_grouped    = num(g(r, "conformal_cov_grouped") %||%
                             g(r, "conformal_cov_grouped_split")),
        stringsAsFactors = FALSE)
    }
  })
  d <- do.call(rbind, Filter(Negate(is.null), rows))
  d$model <- factor(d$model, levels = MODEL_LEVS[MODEL_LEVS %in% d$model])
  d
}

compose4 <- function(pA, pB, pC, pD, heights = c(1, 1)) {
  ((pA | pB) / (pC | pD)) +
    plot_layout(heights = heights, guides = "collect") +
    plot_annotation(tag_levels = "A") &
    paper_tag_theme &
    shared_legend &
    theme(plot.margin = margin(t = 14, r = 10, b = 10, l = 16),
          legend.box.margin = margin(t = 2, r = 0, b = 4, l = 0))
}

# ============================================================================
# F1 (paper Fig. 2): AURC dumbbell. Overlay models with shape (no per-model
# facet) so 14 row labels stay one column. Local compose (not compose4) uses
# tighter margins so the data area, not the tag gutter, takes the canvas.
# ============================================================================
SPLIT_F1 <- c("random", "grouped/time")
# KBS preprint \linewidth ~390 pt (~5.42 in). Height is capped so
# figure+caption stays inside \textheight (taller canvases overflow by >200 pt).
W_F12 <- 5.42
H_F12 <- 5.80
f12_panel <- theme(
  plot.title   = element_text(size = 10, margin = margin(b = 1)),
  axis.text.y  = element_text(size = 8.5, colour = "black", lineheight = 1.05),
  plot.margin  = margin(t = 4, r = 2, b = 0, l = 4),
  legend.position = "bottom"
)
compose_f12 <- function(pA, pB, pC, pD) {
  ((pA | pB) / (pC | pD) / (guide_area() + labs(tag = NULL))) +
    plot_layout(heights = c(1, 1, 0.12), guides = "collect") +
    plot_annotation(tag_levels = "A") &
    theme(
      plot.tag = element_text(family = PAPER_FONT, face = "bold",
                              size = 11, colour = "black"),
      plot.tag.position = "topleft",
      plot.margin = margin(t = 8, r = 4, b = 2, l = 6),
      legend.position = "bottom",
      legend.direction = "horizontal",
      legend.box = "horizontal",
      legend.margin = margin(0, 0, 0, 0),
      legend.box.spacing = unit(2, "pt")
    )
}

make_dumbbell <- function(d, ttl) {
  m <- rbind(
    data.frame(model = d$model, name = d$name, split = "random",
               aurc = d$aurc_random, stringsAsFactors = FALSE),
    data.frame(model = d$model, name = d$name, split = "grouped/time",
               aurc = d$aurc_grouped, stringsAsFactors = FALSE))
  m$split <- factor(m$split, levels = SPLIT_F1)
  m$model <- factor(as.character(m$model), levels = MODEL_LEVS)
  n_mod <- nlevels(droplevels(m$model))
  p <- ggplot(m, aes(aurc, reorder(name, aurc))) +
    geom_line(aes(group = interaction(model, name)), colour = "grey70",
              linewidth = 0.4) +
    geom_point(aes(colour = split, shape = model), size = 2.0) +
    scale_colour_manual(values = c("random" = okabe_ito[1],
                                   "grouped/time" = okabe_ito[2]),
                        breaks = SPLIT_F1) +
    scale_shape_manual(values = SHAPE_VALS, drop = TRUE) +
    scale_x_log10() +
    scale_y_discrete(expand = expansion(add = 0.22)) +
    labs(title = ttl, x = "AURC (log; lower=better)", y = NULL,
         colour = "Split", shape = "Model") +
    guides(colour = guide_legend(order = 1, nrow = 1),
           shape  = guide_legend(order = 2, nrow = 1)) +
    theme_paper() + f12_panel
  if (n_mod == 1) {
    p <- p + guides(shape = "none")
  }
  p
}
dfKI  <- arm_df(S2KI)
dfFM  <- arm_df(FM, "TabICLv2")
dfDPT <- arm_df(DPT, "TabDPT")
dfGB  <- arm_df(GBMB)
f1 <- compose_f12(
  make_dumbbell(dfKI,  "GBMs, key included"),
  make_dumbbell(dfFM,  "TabICLv2"),
  make_dumbbell(dfDPT, "TabDPT"),
  make_dumbbell(dfGB,  "Tuned GBMs"))
if (want_fig("F1"))
  save_fig(f1, file.path(SDIR, "F1_aurc_random_vs_grouped"), w = W_F12, h = H_F12)
cat("F1: n rows GBM=", nrow(dfKI), " FM=", nrow(dfFM), " DPT=", nrow(dfDPT),
    " TunedGBM=", nrow(dfGB), "\n")

# ============================================================================
# F2 (paper Fig. 3): repair ratio. Global model colour/shape so patchwork
# collects one four-key legend instead of a GBM legend plus an FM legend.
# ============================================================================
make_repair <- function(d, ttl) {
  d <- d[is.finite(d$repair_grouped), c("name", "repair_grouped", "model")]
  d$model <- factor(as.character(d$model), levels = MODEL_LEVS)
  ggplot(d, aes(reorder(name, repair_grouped), repair_grouped, colour = model,
                shape = model)) +
    geom_hline(yintercept = 0, linetype = 2, colour = "grey60") +
    geom_point(size = 2.2, position = position_dodge(width = 0.45), na.rm = TRUE) +
    coord_flip() +
    scale_colour_manual(values = COLOR_VALS, breaks = MODEL_LEVS, drop = FALSE) +
    scale_shape_manual(values = SHAPE_VALS, breaks = MODEL_LEVS, drop = FALSE) +
    scale_x_discrete(expand = expansion(add = 0.22)) +
    labs(title = ttl, x = NULL, y = "Grouped repair ratio",
         colour = "Model", shape = "Model") +
    guides(colour = guide_legend(nrow = 1, override.aes = list(size = 2.4)),
           shape  = "none") +
    theme_paper() + f12_panel
}
dfKE   <- arm_df(S2KE)
dfFMKE <- arm_df(FMKE, "TabICLv2")
dfFM2  <- rbind(dfFM, dfDPT)
dfFM2$model <- factor(as.character(dfFM2$model), levels = MODEL_LEVS)
f2 <- compose_f12(
  make_repair(dfKI,   "GBMs, key included"),
  make_repair(dfFM2,  "TabICLv2 + TabDPT"),
  make_repair(dfKE,   "GBMs, key excluded"),
  make_repair(dfFMKE, "TabICLv2, key excluded"))
if (want_fig("F2"))
  save_fig(f2, file.path(SDIR, "F2_repair_ratio"), w = W_F12, h = H_F12)
cat("F2: KI=", nrow(dfKI), " FM2=", nrow(dfFM2), " KE=", nrow(dfKE),
    " FMKE=", nrow(dfFMKE), "\n")
if (P4_ONLY %in% c("F1", "F2", "F12")) {
  cat("P4_ONLY=", P4_ONLY, ": stopping before F3-F6\n", sep = "")
  quit(save = "no")
}
# ============================================================================
# F3 (paper Fig. 4): model agnosticism. Do not use compose4: `& shared_legend`
# forces a legend onto every panel, so collect concatenates B+C+D copies and
# clips the row ("GBoost", "Ta..."). One legend from panel B (all four
# families); C/D suppress theirs. Equal row heights so B's 14 labels get the
# same slot as C/D. TabDPT has no key-excluded coverage JSON — do not invent
# points; the shared legend still names the family used in B.
# ============================================================================
cov_from <- function(res, cov_key, label = NULL) {
  do.call(rbind, lapply(res$results, function(r) {
    cv <- num(g(r, cov_key))
    nm <- as.character(g(r, "name"))
    ok <- is.null(r$status) || r$status == "ok"
    if (ok && !is.na(cv) && (is.null(KEYED14) || nm %in% KEYED14)) {
      data.frame(model = pretty_model(label %||% as.character(g(r, "model"))),
                 name  = pretty_dataset(nm),
                 cov   = cv,
                 stringsAsFactors = FALSE)
    }
  }))
}
cov4_ki <- rbind(
  cov_from(S2KI, "conformal_cov_grouped_split"),
  cov_from(FM,   "conformal_cov_grouped", "TabICLv2"),
  cov_from(DPT,  "conformal_cov_grouped", "TabDPT"))
cov4_ke <- rbind(
  cov_from(S2KE, "conformal_cov_grouped_split"),
  cov_from(FMKE, "conformal_cov_grouped", "TabICLv2"))
gbm_cov_gb <- cov_from(GBMB, "conformal_cov_grouped")
gbm_cov_gb <- gbm_cov_gb[gbm_cov_gb$name %in% pretty_dataset(KEYED14), ]
# Shared y-order (table roster) so B/C/D are row-aligned.
ds_lev <- rev(pretty_dataset(KEYED14))

xs <- dfKI[dfKI$model == "XGBoost",  c("name", "aurc_grouped")]; names(xs)[2] <- "xgboost"
ls <- dfKI[dfKI$model == "LightGBM", c("name", "aurc_grouped")]; names(ls)[2] <- "lightgbm"
w  <- merge(xs, ls, by = "name")
pA3 <- ggplot(w, aes(xgboost, lightgbm)) +
  geom_abline(slope = 1, intercept = 0, linetype = 2, colour = "grey60") +
  geom_point(size = 2.2, colour = okabe_ito[1]) +
  scale_x_log10() + scale_y_log10() +
  labs(title = "Grouped AURC",
       x = "Grouped AURC, XGBoost (log)",
       y = "Grouped AURC, LightGBM (log)") +
  theme_paper() +
  theme(plot.title = element_text(size = 10, margin = margin(b = 2)),
        plot.margin = margin(t = 6, r = 6, b = 2, l = 6),
        legend.position = "none")

make_cov_panel <- function(d, ttl) {
  d$model <- factor(as.character(d$model), levels = MODEL_LEVS)
  d$name  <- factor(d$name, levels = ds_lev)
  p <- ggplot(d, aes(name, cov, colour = model, shape = model)) +
    geom_hline(yintercept = 0.90, linetype = 2, colour = "grey50",
               linewidth = 0.5) +
    geom_point(size = 2.0, position = position_dodge(0.5)) +
    scale_colour_manual(values = COLOR_VALS, breaks = MODEL_LEVS, drop = FALSE) +
    scale_shape_manual(values = SHAPE_VALS, breaks = MODEL_LEVS, drop = FALSE) +
    scale_y_continuous(limits = c(0.15, 1.02), breaks = seq(0.2, 1.0, 0.2),
                       expand = expansion(mult = c(0.02, 0.04))) +
    coord_flip(clip = "off") +
    labs(title = ttl, x = NULL, y = "Grouped coverage (target 0.90)",
         colour = NULL, shape = NULL) +
    theme_paper() +
    theme(plot.title = element_text(size = 10, margin = margin(b = 2)),
          plot.margin = margin(t = 6, r = 8, b = 2, l = 6),
          axis.text.y = element_text(size = 9, colour = "black",
                                     lineheight = 0.95),
          legend.position = "none")
  p <- p + guides(
    colour = guide_legend(nrow = 1, byrow = TRUE,
                          override.aes = list(size = 2.4)),
    shape  = "none")
  p
}
pB3 <- make_cov_panel(cov4_ki, "Key included")
pC3 <- make_cov_panel(cov4_ke, "Key excluded")
pD3 <- make_cov_panel(gbm_cov_gb, "Tuned GBM")
# Fully free A so its log–log axes are not aligned to B's dataset names.
# guide_area() is a third row so the collected 4-key legend sits under the 2x2
# (a bottom legend on B alone lands between the rows).
f3 <- (free(pA3) | pB3) / (pC3 | pD3) / (guide_area() + labs(tag = NULL)) +
  plot_layout(heights = c(1, 1, 0.16), guides = "collect",
              axes = "keep", axis_titles = "keep") +
  plot_annotation(tag_levels = "A") &
  theme(
    plot.tag = element_text(family = PAPER_FONT, face = "bold",
                            size = 11, colour = "black"),
    plot.tag.position = "topleft",
    plot.margin = margin(t = 10, r = 8, b = 2, l = 10),
    legend.position = "bottom",
    legend.direction = "horizontal",
    legend.box = "horizontal",
    legend.margin = margin(0, 0, 0, 0),
    legend.box.spacing = unit(2, "pt"),
    legend.key.width = unit(12, "pt"),
    legend.key.height = unit(12, "pt"),
    legend.key.spacing.x = unit(12, "pt")
  )
if (want_fig("F3"))
  save_fig(f3, file.path(SDIR, "F3_model_agnostic"), w = W_F12, h = 8.00)
cat("F3: scatter n=", nrow(w), " cov4_ki=", nrow(cov4_ki), " cov4_ke=", nrow(cov4_ke),
    " gbmb=", nrow(gbm_cov_gb),
    " models_C=", paste(sort(unique(as.character(cov4_ke$model))), collapse = ","),
    "\n")
if (P4_ONLY %in% c("F3")) {
  cat("P4_ONLY=F3: stopping before F4-F6\n")
  quit(save = "no")
}
# ============================================================================
# F4: calibration-size diagnostic
# Wider native canvas than the shared W so the 2x2 scatters fill \linewidth
# (KBS preprint ~5.4 in; DMKD sn-jnl similar) without clipping titles/legend.
# Do not use compose4 here: collecting Model+Dataset colour guides onto one
# bar clips the dataset names. F4-only width/height; F5/F6 keep shared W.
# ============================================================================
F4_W <- 7.10
F4_H <- 5.15
calsize_panel <- function(diag, ttl, ylab = "Mondrian Δcov") {
  fr <- do.call(rbind, lapply(diag$rows, function(r) data.frame(
    cal  = num(g(r, "uncbin_cal_median")),
    mond = num(g(r, "mondrian_improvement_med")),
    stringsAsFactors = FALSE)))
  fr <- fr[is.finite(fr$cal) & is.finite(fr$mond), ]
  rho <- suppressWarnings(cor(fr$cal, fr$mond, method = "spearman"))
  p <- ggplot(fr, aes(cal, mond)) +
    geom_hline(yintercept = 0, linetype = 3, colour = "grey50") +
    geom_point(size = 2.8, colour = okabe_ito[4]) +
    geom_smooth(method = "lm", formula = y ~ x, se = TRUE,
                colour = okabe_ito[1], linewidth = 0.7) +
    scale_x_log10(expand = expansion(mult = c(0.03, 0.05))) +
    scale_y_continuous(expand = expansion(mult = c(0.04, 0.08))) +
    labs(title = sprintf("%s  (rho = %.2f, n = %d)", ttl, rho, nrow(fr)),
         x = "Per-bin cal. fold size (log)",
         y = ylab) +
    theme_paper()
  list(plot = p, rho = rho, n = nrow(fr))
}
f4a <- calsize_panel(DIAKI, "Key included")
f4b <- calsize_panel(DIAKE, "Key excluded", ylab = NULL)
fr_all <- do.call(rbind, lapply(DIAKI$rows, function(r) data.frame(
  cal   = num(g(r, "uncbin_cal_median")),
  mond  = num(g(r, "mondrian_improvement_med")),
  model = pretty_model(as.character(g(r, "model"))),
  stringsAsFactors = FALSE)))
fr_all <- fr_all[is.finite(fr_all$cal) & is.finite(fr_all$mond), ]
fr_all$model <- factor(fr_all$model, levels = MODEL_LEVS[MODEL_LEVS %in% fr_all$model])
pC4 <- ggplot(fr_all, aes(cal, mond, colour = model, shape = model)) +
  geom_hline(yintercept = 0, linetype = 3, colour = "grey50") +
  geom_point(size = 2.8) +
  scale_color_paper() +
  scale_shape_manual(values = c(16, 17, 15, 18)) +
  scale_x_log10(expand = expansion(mult = c(0.03, 0.05))) +
  scale_y_continuous(expand = expansion(mult = c(0.04, 0.08))) +
  labs(title = sprintf("By model  (n = %d)", nrow(fr_all)),
       x = "Per-bin cal. fold size (log)",
       y = "Mondrian Δcov",
       colour = "Model", shape = "Model") +
  theme_paper()
plan_lgb <- lapply(PLAN$rows, function(r) {
  if (as.character(g(r, "rule")) == "floor1" && as.character(g(r, "model")) == "lightgbm")
    data.frame(name = pretty_dataset(as.character(g(r, "name"))),
               side = as.character(g(r, "side")),
               frac = num(g(r, "frac")),
               mond = num(g(r, "mondrian_improvement_med")),
               stringsAsFactors = FALSE)
})
plan_df  <- do.call(rbind, Filter(Negate(is.null), plan_lgb))
plan_agg <- aggregate(mond ~ name + side + frac, data = plan_df, FUN = median)
plan_agg$side <- factor(plan_agg$side,
                        levels = c("helps", "hurts"),
                        labels = c("Helps", "Hurts"))
DS_ALL4 <- sort(unique(plan_agg$name))
DS_COL4 <- setNames(okabe_ito[seq_along(DS_ALL4)], DS_ALL4)
pD4 <- ggplot(plan_agg, aes(factor(frac), mond, colour = name, group = name)) +
  geom_hline(yintercept = 0, linetype = 3, colour = "grey50") +
  geom_line(linewidth = 0.7) + geom_point(size = 2.3) +
  scale_colour_manual(values = DS_COL4) +
  scale_x_discrete(labels = function(x) {
    v <- as.numeric(as.character(x))
    ifelse(abs(v - 1) < 1e-9, "1", format(v, trim = TRUE))
  }) +
  scale_y_continuous(expand = expansion(mult = c(0.04, 0.08))) +
  facet_wrap(~side, ncol = 2) +
  labs(title = "Within-dataset sweep (LightGBM)",
       x = "Calibration fraction", y = NULL,
       colour = "Dataset") +
  guides(colour = guide_legend(nrow = 2, byrow = TRUE)) +
  theme_paper() +
  theme(panel.spacing.x = unit(10, "pt"),
        axis.text.x = element_text(size = 9))
# Keep Model (C) and Dataset (D) as separate legend rows spanning the full
# width so the six dataset names are not clipped at the panel edge.
f4 <- ((f4a$plot | f4b$plot) / (pC4 | pD4)) +
  plot_layout(heights = c(1, 1.10), guides = "collect") +
  plot_annotation(tag_levels = "A") &
  paper_tag_theme &
  theme(
    legend.position = "bottom",
    legend.box = "vertical",
    legend.justification = "center",
    legend.margin = margin(t = 1, r = 4, b = 0, l = 4),
    plot.margin = margin(t = 14, r = 20, b = 6, l = 16)
  )
if (want_fig("F4"))
  save_fig(f4, file.path(SDIR, "F4_calsize_vs_mondrian"), w = F4_W, h = F4_H)
cat("F4: A n=", f4a$n, " rho=", round(f4a$rho, 3), " B n=", f4b$n,
    " C n=", nrow(fr_all), " D n=", nrow(plan_agg),
    " canvas=", F4_W, "x", F4_H, "in\n")
if (P4_ONLY %in% c("F4")) {
  cat("P4_ONLY=F4: stopping before F5-F6\n")
  quit(save = "no")
}

# ============================================================================
# F5: TableShift A|B only. Body/caption cite A and B; C/D are not in-text.
# Canonical generator: p5_tableshift.R (Makefile `make figures`).
# ============================================================================
if (want_fig("F5")) {
  sys.source(file.path(SDIR, "p5_tableshift.R"), envir = new.env())
}
if (P4_ONLY %in% c("F5")) {
  cat("P4_ONLY=F5: stopping before F6\n")
  quit(save = "no")
}

# ============================================================================
# F6: split-realization fragility — Stage-2 2x2 (model x key condition)
# A LightGBM key-included   B XGBoost key-included
# C LightGBM key-excluded   D XGBoost key-excluded
# Stage-1 is XGBoost-only (no LightGBM arm). After RNG reconciliation its
# key-included single-draw records match Stage-2 XGBoost; the K=30 split-repeat
# majority-robust fraction (83%) is the upper end of the 75-83% range in the
# text, not a fourth visual factor. Do not wire panel D to stage1_xgboost.
# ============================================================================
MAJ <- num(g(AGG, "majority_threshold"))
mk_dist <- function(node, label) {
  data.frame(metric = label, count = as.integer(vec(node$per_k)),
             stringsAsFactors = FALSE)
}
frag_arm <- function(node) {
  d <- rbind(
    mk_dist(node$grouped_gap_count,   "Grouped-gap"),
    mk_dist(node$repair_count,        "Repair beats random"),
    mk_dist(node$aurc_degrade_count,  "AURC-degrade"),
    mk_dist(node$undercover_count,    "Under-coverage"))
  d$metric <- factor(d$metric, levels = c(
    "Grouped-gap", "AURC-degrade", "Under-coverage", "Repair beats random"))
  d[is.finite(d$count) & d$count > 0, ]
}
d_lgb_ki <- frag_arm(AGG$stage2$key_included$lightgbm)
d_xgb_ki <- frag_arm(AGG$stage2$key_included$xgboost)
d_lgb_ke <- frag_arm(AGG$stage2$key_excluded$lightgbm)
d_xgb_ke <- frag_arm(AGG$stage2$key_excluded$xgboost)
# Shared y-scale: all four arms are Stage-2 (K=20).
YMAX <- max(vapply(list(d_lgb_ki, d_xgb_ki, d_lgb_ke, d_xgb_ke), function(d) {
  max(as.integer(table(interaction(d$count, d$metric, drop = TRUE))))
}, integer(1L)))
make_frag_panel <- function(d, ttl) {
  ggplot(d, aes(count, fill = metric)) +
    geom_bar(position = position_dodge(width = 1.0, preserve = "single"),
             width = 0.96, colour = "white", linewidth = 0.15) +
    geom_vline(xintercept = MAJ - 0.5, linetype = 2, colour = "grey25",
               linewidth = 0.75) +
    annotate("text", x = MAJ - 0.5, y = Inf,
             label = paste0("majority = ", MAJ), hjust = 1.12,
             vjust = 1.25, size = 3.6, colour = "black", family = PAPER_FONT) +
    scale_fill_paper() +
    scale_x_continuous(breaks = seq(2, 14, 2)) +
    scale_y_continuous(breaks = seq(0, 16, 4),
                       expand = expansion(mult = c(0, 0.06))) +
    coord_cartesian(xlim = c(1.4, 14.6), ylim = c(0, YMAX * 1.06),
                    clip = "off") +
    labs(title = ttl, x = "Count (of 14 datasets)", y = "Split draws",
         fill = NULL) +
    guides(fill = guide_legend(nrow = 1, byrow = TRUE)) +
    theme_paper() +
    theme(plot.title = element_text(size = 11),
          axis.title = element_text(size = 11),
          axis.text = element_text(size = 10),
          legend.text = element_text(size = 10),
          panel.border = element_rect(linewidth = 0.75, colour = "grey30"),
          axis.ticks = element_line(linewidth = 0.55, colour = "grey30"),
          axis.ticks.length = unit(2.6, "pt"),
          plot.margin = margin(t = 2, r = 2, b = 0, l = 4))
}
# F6-local compose: collect one legend and shared axis titles so the 2x2
# fills the column (compose4 keeps per-panel titles for F1-F5).
f6 <- (
  (make_frag_panel(d_lgb_ki, "LightGBM, Stage-2, key included") |
   make_frag_panel(d_xgb_ki, "XGBoost, Stage-2, key included")) /
  (make_frag_panel(d_lgb_ke, "LightGBM, Stage-2, key excluded") |
   make_frag_panel(d_xgb_ke, "XGBoost, Stage-2, key excluded"))
) +
  plot_layout(guides = "collect", axis_titles = "collect") +
  plot_annotation(tag_levels = "A") &
  paper_tag_theme &
  shared_legend &
  theme(plot.margin = margin(t = 4, r = 2, b = 0, l = 8),
        legend.margin = margin(t = 0, r = 0, b = 0, l = 0),
        legend.box.margin = margin(t = -8, r = 0, b = 0, l = 0),
        legend.position = "bottom",
        panel.border = element_rect(linewidth = 0.75, colour = "grey30"))
if (want_fig("F6"))
  save_fig(f6, file.path(SDIR, "F6_split_repeats_fragility"), w = W, h = 5.40)
cat("F6: lgb_ki=", nrow(d_lgb_ki), " xgb_ki=", nrow(d_xgb_ki),
    " lgb_ke=", nrow(d_lgb_ke), " xgb_ke=", nrow(d_xgb_ke), "\n")
cat("All expansions done.\n")
