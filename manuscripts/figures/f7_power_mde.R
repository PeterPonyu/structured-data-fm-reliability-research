# F7: post-hoc power / MDE for the Stage-2 conjunctive count gate (4 panels).
#
# Reads ONLY experiments/power_analysis_2026-08-01/results.json (frozen,
# deterministic -- exact Poisson-binomial by DP convolution, manifest rng_used
# = FALSE, refits = 0). Nothing here is simulated at draw time.
#
# HONESTY NOTE -- this is a POST-HOC power read on observed per-dataset flip
# frequencies p_hat_i, not an a-priori design calculation, and the figure must
# not be drawn to look like the latter. Three caveats are given panel space
# rather than buried in the caption:
#   * the independence idealisation OVERSTATES power. Panel B shows why: the
#     Poisson-binomial pmf (0.909) sits above the empirical pass fraction
#     (0.833) because it captures unequal p_i but NOT the positive
#     cross-dataset dependence within a split draw. Observed overdispersion
#     vs Poisson-binomial is 1.45x.
#   * the 0.83 read leans on the always-flagging datasets. Panel D is the
#     leave-one-out fragility: zeroing electricity (or adult, same p_hat = 1.0)
#     drops power to 0.652, BELOW the 0.8 target. That is drawn as a crossing
#     of the target line, not smoothed away.
#   * the uniform-p MDE (panel C) is the claim that survives leave-one-out,
#     because it carries no per-dataset structure. It is labelled as the
#     robust statement to keep the reader from over-reading panel A.
cargs <- commandArgs(trailingOnly = FALSE)
SDIR  <- dirname(normalizePath(sub("^--file=", "", cargs[grep("^--file=", cargs)][1])))
source(Sys.getenv("GGTHEME_R", file.path(SDIR, "ggtheme.R")))
library(patchwork)

REPO <- normalizePath(file.path(SDIR, "..", ".."))
PW   <- read_result(file.path(REPO, "experiments", "power_analysis_2026-08-01",
                              "results.json"))

num <- function(x) if (is.null(x)) NA_real_ else suppressWarnings(as.numeric(x))
g   <- function(r, k) if (!is.null(r[[k]])) r[[k]] else NA
# JSON arrays come back as lists of length-1 elements; flatten to atomic.
vec <- function(x) unlist(x, use.names = FALSE)

MAJ    <- num(g(PW$threshold, "majority"))       # 8
NDS    <- num(g(PW$threshold, "n_datasets"))     # 14
TARGET <- num(g(PW$threshold, "target_power"))   # 0.8

# ---- panel A: per-dataset flip frequency, the input the power read rests on --
# Ordered by p_hat so the bimodality is visible: the gate's power comes from a
# handful of always-flagging datasets, not from a uniform tendency across 14.
EX <- PW$extracted
pa <- data.frame(
  name = vec(EX$datasets),
  p    = vec(EX$gap_p_hat),
  n_k  = vec(EX$per_dataset_n_k),
  stringsAsFactors = FALSE)
pa <- pa[order(pa$p), ]
pa$name <- factor(pa$name, levels = pa$name)
# Wilson interval on p_hat from the actual per-dataset draw count: these are
# 28-30 draws, so the point estimates are not tight and the figure should not
# present them as if they were.
wilson <- function(p, n, z = 1.96) {
  cen <- (p + z^2 / (2 * n)) / (1 + z^2 / n)
  hw  <- z * sqrt(p * (1 - p) / n + z^2 / (4 * n^2)) / (1 + z^2 / n)
  c(max(0, cen - hw), min(1, cen + hw))
}
wl <- t(mapply(wilson, pa$p, pa$n_k))
pa$lo <- wl[, 1]; pa$hi <- wl[, 2]
p_mean <- num(g(EX, "gap_p_hat_mean"))

f7a <- ggplot(pa, aes(p, name)) +
  geom_vline(xintercept = p_mean, linetype = 2, colour = "grey40") +
  # y pinned to a real factor level: a numeric y here makes ggplot treat the
  # discrete dataset axis as continuous and the build fails.
  annotate("text", x = p_mean, y = levels(pa$name)[1],
           label = paste0("mean = ", sprintf("%.2f", p_mean)),
           hjust = -0.08, vjust = -0.9, size = 3.2, colour = "black",
           family = PAPER_FONT) +
  geom_errorbar(aes(xmin = lo, xmax = hi), orientation = "y", width = 0,
                linewidth = 0.4, colour = "grey55") +
  geom_point(size = 2.1, colour = okabe_ito[1]) +
  scale_x_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.25)) +
  labs(x = expression("per-dataset flip frequency  " * hat(p)[i]), y = NULL,
       subtitle = "Gate input is bimodal, not uniform") +
  theme_paper()

# ---- panel B: modelled pmf vs the 30 observed counts ------------------------
# The whole reconciliation lives here. Bars = exact Poisson-binomial pmf under
# independence; points = empirical frequency of each count over the 30 split
# draws. The model puts more mass at/above 8 than the draws did, which is the
# 0.909 vs 0.833 discrepancy, and it is shown rather than asserted.
pmf <- data.frame(k = seq_along(vec(PW$power_at_observed$gap_pmf)) - 1,
                  pmf = vec(PW$power_at_observed$gap_pmf))
# k = 0..3 carry exactly zero modelled mass and no observed draws. They are
# dropped explicitly, with the count asserted below, rather than left to be
# silently clipped by the axis limits.
PMF_XMIN <- 3.5
n_zero_dropped <- sum(pmf$k < PMF_XMIN)
PMF_DROP_TOL <- 1e-4
dropped_mass <- sum(pmf$pmf[pmf$k < PMF_XMIN])
stopifnot(dropped_mass < PMF_DROP_TOL, min(vec(EX$per_k_gap)) > PMF_XMIN)
pmf <- pmf[pmf$k > PMF_XMIN, ]
obs_k <- vec(EX$per_k_gap)
emp <- as.data.frame(table(factor(obs_k, levels = pmf$k)),
                     stringsAsFactors = FALSE)
names(emp) <- c("k", "n"); emp$k <- as.integer(as.character(emp$k))
emp$frac <- emp$n / length(obs_k)

pow_pb  <- num(g(PW$power_at_observed, "gap_arm_poisson_binomial"))
pow_emp <- num(g(PW$power_at_observed, "empirical_recomputed_from_per_k"))
od      <- num(g(PW$variance_decomposition, "overdispersion_vs_poisson_binomial"))

f7b <- ggplot(pmf, aes(k, pmf)) +
  # Shade the passing region so ">=8 of 14" is a region, not an arithmetic step.
  annotate("rect", xmin = MAJ - 0.5, xmax = 14.5,
           ymin = -Inf, ymax = Inf, fill = "grey85", alpha = 0.55) +
  geom_col(width = 0.72, fill = okabe_ito[3], colour = NA) +
  geom_point(data = emp[emp$frac > 0, ], aes(k, frac), size = 2.1,
             colour = okabe_ito[2], inherit.aes = FALSE) +
  geom_vline(xintercept = MAJ - 0.5, linetype = 2, colour = "grey30") +
  annotate("text", x = MAJ - 0.4, y = Inf, hjust = -0.05, vjust = 1.6,
           label = "gate passes", size = 3.2, colour = "black",
           family = PAPER_FONT) +
  scale_x_continuous(breaks = seq(4, 14, 2), limits = c(PMF_XMIN, 14.5)) +
  labs(x = "datasets flagged, k (of 14)", y = "probability / frequency",
       subtitle = sprintf("Model %.3f overstates draws %.3f (%.2fx overdispersed)",
                          pow_pb, pow_emp, od)) +
  theme_paper()

# ---- panel C: power vs uniform p, and the MDE crossing ----------------------
# This is the leave-one-out-immune statement (robustness/uniform_p_robust_claim),
# so it is the panel a reader should carry away. MDE and target both read from
# the frozen JSON -- no hardcoded 0.64.
pc  <- do.call(rbind, lapply(PW$power_curve_uniform_p, function(r) data.frame(
  p = num(g(r, "p")), power = num(g(r, "power")), stringsAsFactors = FALSE)))
mde <- num(g(PW$mde, "min_uniform_p_for_80pct_power"))

f7c <- ggplot(pc, aes(p, power)) +
  geom_hline(yintercept = TARGET, linetype = 2, colour = "grey40") +
  geom_vline(xintercept = mde, linetype = 3, colour = okabe_ito[6]) +
  geom_line(linewidth = 0.7, colour = okabe_ito[6]) +
  geom_point(size = 1.6, colour = okabe_ito[6]) +
  # Mark where the observed mean p_hat sits relative to the MDE: barely past it,
  # which is the honest read and the reason the gate is not comfortably powered.
  geom_point(data = data.frame(p = p_mean,
                               power = num(g(PW$binomial_sanity_check, "power"))),
             size = 2.6, shape = 21, stroke = 0.9,
             colour = "black", fill = okabe_ito[2]) +
  annotate("text", x = p_mean, y = num(g(PW$binomial_sanity_check, "power")),
           label = "observed mean", hjust = 1.12, vjust = 1.9, size = 3.1,
           colour = "black", family = PAPER_FONT) +
  annotate("text", x = mde, y = 0.06, label = sprintf("MDE = %.3f", mde),
           hjust = -0.07, size = 3.2, colour = "black", family = PAPER_FONT) +
  annotate("text", x = min(pc$p), y = TARGET, label = "80% target",
           hjust = -0.04, vjust = -0.6, size = 3.1, colour = "black",
           family = PAPER_FONT) +
  scale_y_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.25)) +
  labs(x = "uniform per-dataset flip probability p", y = "gate power",
       subtitle = sprintf("MDE = %.3f; observed mean %.2f barely clears it",
                          mde, p_mean)) +
  theme_paper()

# ---- panel D: leave-one-out fragility of the per-dataset read ---------------
# Ordered by the damage done. Segment = power if that dataset's p_i is set to 0
# (never flags) through p_i set to 1 (always flags); the target line crossing is
# the point of the panel.
loo <- do.call(rbind, lapply(PW$robustness$single_dataset_influence,
  function(r) data.frame(name = as.character(g(r, "dataset")),
    p0 = num(g(r, "power_if_p_set_0")), p1 = num(g(r, "power_if_p_set_1")),
    stringsAsFactors = FALSE)))
loo <- loo[order(loo$p0), ]
loo$name <- factor(loo$name, levels = loo$name)
# Datasets whose removal alone sinks the gate below target: called out by fill,
# because "which ones" is the actionable part of the caveat.
loo$breaks <- loo$p0 < TARGET
worst <- as.character(g(PW$robustness, "most_influential_dataset"))

f7d <- ggplot(loo, aes(y = name)) +
  geom_vline(xintercept = TARGET, linetype = 2, colour = "grey40") +
  geom_segment(aes(x = p0, xend = p1, yend = name), linewidth = 0.45,
               colour = "grey60") +
  geom_point(aes(x = p1), size = 1.5, shape = 21, fill = "white",
             colour = "grey45", stroke = 0.5) +
  geom_point(aes(x = p0, colour = breaks), size = 2.1) +
  # Vermillion = this dataset alone sinks the gate below target; grey = it does
  # not. Yellow was tried here and rejected: it is the lowest-contrast hue in the
  # palette on white and read as benign for what is the figure's warning.
  scale_colour_manual(values = c(`TRUE` = okabe_ito[4], `FALSE` = "grey45"),
                      guide = "none") +
  annotate("text", x = TARGET, y = levels(loo$name)[nrow(loo)],
           label = "80% target", hjust = 1.06, vjust = 0.2, size = 3.1,
           colour = "black", family = PAPER_FONT) +
  scale_x_continuous(limits = c(0.5, 1.02), breaks = seq(0.5, 1, 0.1)) +
  labs(x = "gate power if one dataset never flags (solid)\nor always flags (hollow)",
       y = NULL,
       subtitle = sprintf("%d of %d datasets sink the gate alone", sum(loo$breaks),
                          nrow(loo))) +
  theme_paper()

# ---- assemble ---------------------------------------------------------------
f7 <- (f7a | f7b) / (f7c | f7d) + plot_annotation(tag_levels = "A") &
  paper_tag_theme
save_fig(f7, file.path(SDIR, "F7_power_mde"), w = 6.5, h = 5.2)

# ---- provenance / counts to stdout -----------------------------------------
cat("F7 panel A: n datasets=", nrow(pa),
    " p_hat range=", sprintf("%.4f", min(pa$p)), "-", sprintf("%.4f", max(pa$p)),
    " mean=", sprintf("%.4f", p_mean),
    " draws per dataset=", paste(sort(unique(pa$n_k)), collapse = "/"), "\n")
cat("F7 panel A p_hat at the extremes (the bimodality the gate leans on):",
    sum(pa$p >= 0.9), "datasets >=0.9,", sum(pa$p <= 0.1), "datasets <=0.1\n")
cat("F7 panel B: negligible-mass bins dropped (k<", PMF_XMIN, ")=", n_zero_dropped,
    " total mass dropped=", sprintf("%.2e", dropped_mass), "(tol", PMF_DROP_TOL, ")\n")
cat("F7 panel B: n split draws=", length(obs_k),
    " observed k range=", min(obs_k), "-", max(obs_k),
    " plotted pmf mass=", sprintf("%.6f", sum(pmf$pmf)), "\n")
cat("F7 panel B power reconciliation: poisson-binomial=", sprintf("%.4f", pow_pb),
    " empirical=", sprintf("%.4f", pow_emp),
    " diff=", sprintf("%+.4f", num(g(PW$power_at_observed,
                                     "poisson_binomial_minus_empirical"))),
    " overdispersion=", sprintf("%.3f", od), "x\n")
cat("F7 panel C: n curve points=", nrow(pc),
    " MDE(uniform p for 80% power)=", sprintf("%.4f", mde),
    " expected count at MDE=", sprintf("%.3f", num(g(PW$mde,
                                        "expected_count_at_mde"))), "\n")
cat("F7 panel D: n datasets=", nrow(loo),
    " power range zeroing one=", sprintf("%.4f", min(loo$p0)), "-",
    sprintf("%.4f", max(loo$p0)),
    " n sinking gate below target alone=", sum(loo$breaks),
    " most influential=", worst, "\n")
cat("F7 gate: >=", MAJ, "of", NDS, "datasets, target power", TARGET, "\n")
cat("F7 source: experiments/power_analysis_2026-08-01/results.json",
    "(script_sha256", substr(as.character(g(PW$manifest, "script_sha256")), 1, 12),
    "| rng_used", as.character(g(PW$manifest, "rng_used")),
    "| refits", as.character(g(PW$manifest, "refits")), ")\n")
