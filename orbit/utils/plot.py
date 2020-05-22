# the following lines are added to fix unit test error
# or else the following line will give the following error
# TclError: no display name and no $DISPLAY environment variable
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
import numpy as np
from copy import deepcopy

from orbit.constants.constants import PredictedComponents
from orbit.utils.utils import is_empty_dataframe
from orbit.constants.palette import QualitativePalette


if os.environ.get('DISPLAY', '') == '':
    print('no display found. Using non-interactive Agg backend')
    matplotlib.use('Agg')


def plot_predicted_data(training_actual_df, predicted_df, date_col, actual_col, pred_col,
                        title="", test_actual_df=None, pred_quantiles_col=[],
                        is_visible=True, figsize=None, path=None):
    """
    plot training actual response together with predicted data; if actual response of predicted
    data is there, plot it too.
    Parameters
    ----------
    training_actual_df: pd.DataFrame
        training actual response data frame. two columns required: actual_col and date_col
    predicted_df: pd.DataFrame
        predicted data response data frame. two columns required: actual_col and pred_col. If
        user provide pred_quantiles_col, it needs to include them as well.
    date_col: str
        the date column name
    actual_col: str
    pred_col: str
    title: str
        title of the plot
    test_actual_df: pd.DataFrame
       test actual response dataframe. two columns required: actual_col and date_co
    pred_quantiles_col: list
        a list of two strings for prediction inference where first one for lower quantile and
        the second one for upper quantile
    is_visible: boolean
        whether we want to show the plot. If called from unittest, is_visible might = False.
    figsize: tuple
        figsize pass through to `matplotlib.pyplot.figure()`
    Returns
    -------
        None.
    """

    if is_empty_dataframe(training_actual_df) or is_empty_dataframe(predicted_df):
        raise ValueError("No prediction data or training response to plot.")
    if len(pred_quantiles_col) != 2 and len(pred_quantiles_col) != 0:
        raise ValueError("pred_quantiles_col must be either empty or length of 2.")
    if not set([pred_col] + pred_quantiles_col).issubset(predicted_df.columns):
        raise ValueError("Prediction column(s) not found in predicted df.")
    _training_actual_df = training_actual_df.copy()
    _predicted_df=predicted_df.copy()
    _training_actual_df[date_col] = pd.to_datetime(_training_actual_df[date_col])
    _predicted_df[date_col] = pd.to_datetime(_predicted_df[date_col])

    if not figsize:
        figsize=(16, 8)

    fig, ax = plt.subplots(facecolor='w', figsize=figsize)

    ax.scatter(_training_actual_df[date_col].values,
               _training_actual_df[actual_col].values,
               marker='.', color='black', alpha=0.5, s=70.0,
               label=actual_col)
    ax.plot(_predicted_df[date_col].values,
            _predicted_df[pred_col].values,
            marker=None, color='#12939A', label='prediction')

    if test_actual_df is not None:
        test_actual_df=test_actual_df.copy()
        test_actual_df[date_col] = pd.to_datetime(test_actual_df[date_col])
        ax.scatter(test_actual_df[date_col].values,
                   test_actual_df[actual_col].values,
                   marker='.', color='#FF8C00', alpha=0.5, s=70.0,
                   label=actual_col)

    # prediction intervals
    if pred_quantiles_col:
        ax.fill_between(_predicted_df[date_col].values,
                        _predicted_df[pred_quantiles_col[1]].values,
                        _predicted_df[pred_quantiles_col[0]].values,
                        facecolor='#42999E', alpha=0.2)

    ax.set_title(title, fontsize=16)
    ax.grid(True, which='major', c='gray', ls='-', lw=1, alpha=0.5)
    ax.legend()
    if path:
        plt.savefig(path)
    if is_visible:
        plt.show()


def plot_predicted_components(predicted_df, date_col, figsize=None, path=None):
    """ Plot predicted componenets with the data frame of decomposed prediction where components
    has been pre-defined as `trend`, `seasonality` and `regression`.
    Parameters
    ----------
    predicted_df: pd.DataFrame
        predicted data response data frame. two columns required: actual_col and pred_col. If
        user provide pred_quantiles_col, it needs to include them as well.
    date_col: str
        the date column name
    figsize: tuple
        figsize pass through to `matplotlib.pyplot.figure()`
   Returns
    -------
        None.
    """
    plot_components = [PredictedComponents.TREND.value,
                       PredictedComponents.SEASONALITY.value,
                       PredictedComponents.REGRESSION.value]
    n_panels = len(plot_components)
    if not figsize:
        figsize=(16, 8)

    fig, axes = plt.subplots(n_panels, 1, facecolor='w', figsize=figsize)
    for ax, comp in zip(axes, plot_components):
        x = predicted_df[date_col].dt.to_pydatetime()
        y = predicted_df[comp].values
        ax.plot(x, y, marker=None, color='#12939A')
        ax.grid(True, which='major', c='gray', ls='-', lw=1, alpha=0.2)
        ax.set_title(comp, fontsize=16)
    fig.tight_layout()
    if path:
        plt.savefig(path)


def metric_horizon_barplot(df, model_col='model', pred_horizon_col='pred_horizon',
                           metric_col='smape', bar_width=0.1, path=None):
    plt.rcParams['figure.figsize'] = [20, 6]
    models = df[model_col].unique()
    metric_horizons = df[pred_horizon_col].unique()
    n_models = len(models)
    palette = sns.color_palette("colorblind", n_models)

    # set height of bar
    bars = list()
    for m in models:
        bars.append(list(df[df[model_col] == m][metric_col]))

    # set position of bar on X axis
    r = list()
    r.append(np.arange(len(bars[0])))
    for idx in range(n_models - 1):
        r.append([x + bar_width for x in r[idx]])

    # make the plot
    for idx in range(n_models):
        plt.bar(r[idx], bars[idx], color=palette[idx], width=bar_width, edgecolor='white',
                label=models[idx])

    # add xticks on the middle of the group bars
    plt.xlabel('predict-horizon', fontweight='bold')
    plt.xticks([x + bar_width for x in range(len(bars[0]))], metric_horizons)

    # create legend & show graphic
    plt.legend()
    plt.title("Model Comparison with {}".format(metric_col))

    if path:
        plt.savefig(path)


def plot_posterior_params(mod, kind='density', n_bins=20, ci_level=.95,
                         pair_type='scatter', figsize=None, path=None,
                         incl_trend_params=False, incl_smooth_params=False):
    """ Data Viz for posterior samples

    Params
    ------
    mod : orbit model object
    kind : str, {'density', 'trace', 'pair'}
        which kind of plot to be made. Currently, trace plot may not represent the actual sample process for
        different chainse since this information is not stored in orbit model objects.
    n_bins : int; default 20
        number of bin, used in the histogram plotting
    ci_level : float, between 0 and 1
        confidence interval level
    pair_type : str, {'scatter', 'reg'}
        dot plotting type for off-diagonal plots in pair plot
    figsize : tuple; optional
        figure size
    path : str; optional
        dir path to save the chart
    incl_trend_params : bool
        if plot trend parameters; default False
    incl_smooth_params : bool
        if plot smoothing parameters; default False

    Returns
    -------
    fig : plt object
    """
    if not 'orbit' in str(mod.__class__):
        raise Exception("This plotting utility works for orbit model object only.")
    if mod.infer_method != 'mcmc':
        raise Exception("This plotting utility works for mcmc inference only.")
    if kind not in ['density', 'trace', 'pair']:
        raise Exception("kind must be one of 'density', 'trace', or 'pair'.")

    posterior_samples = deepcopy(mod.posterior_samples)

    if len(mod.positive_regressor_col) > 0:
        for i, regressor in enumerate(mod.positive_regressor_col):
            posterior_samples[regressor] = posterior_samples['pr_beta'][:,i]
    if len(mod.regular_regressor_col) > 0:
        for i, regressor in enumerate(mod.regular_regressor_col):
            posterior_samples[regressor] = posterior_samples['rr_beta'][:, i]

    params_ = mod.positive_regressor_col + mod.regular_regressor_col + ['obs_sigma']
    if incl_trend_params:
        # trend params in LGT or DLT
        params_ += ['gt_pow', 'lt_coef', 'gt_coef', 'gb', 'gl']
    if incl_smooth_params:
        params_ += ['lev_sm', 'slp_sm', 'sea_sm']

    params_ = [x for x in params_ if x in posterior_samples.keys()]

    if not figsize:
        figsize = (8, 2 * len(params_))

    def _density_plot(posterior_samples, n_bins=20, ci_level=.95, figsize=None):

        fig, axes = plt.subplots(len(params_), 1, squeeze=True, figsize=figsize)
        for i, param in enumerate(params_):
            samples = posterior_samples[param]
            mean = np.mean(samples)
            median = np.median(samples)
            cred_min, cred_max = np.percentile(samples, 100 * (1 - ci_level)/2), \
                                    np.percentile(samples, 100 * (1 + ci_level)/2)

            sns.distplot(samples, bins=n_bins, kde_kws={'shade':True}, ax=axes[i], norm_hist=False)
            # sns.kdeplot(samples, shade=True, ax=axes[i])
            axes[i].set_xlabel(param)
            axes[i].set_ylabel('density')
            # draw vertical lines
            axes[i].axvline(mean, color=QualitativePalette['PostQ'].value[0], lw=4, alpha=.5, label='mean')
            axes[i].axvline(median, color=QualitativePalette['PostQ'].value[1], lw=4, alpha=.5, label='median')
            axes[i].axvline(cred_min, linestyle='--', color='k', alpha=.5, label='95% CI')
            axes[i].axvline(cred_max, linestyle='--', color='k', alpha=.5)
            # axes[i].legend()

        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper right', bbox_to_anchor=(1.15, 0.9))
        plt.suptitle('Histogram and Density of Posterior Samples')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        return fig

    def _trace_plot(posterior_samples, ci_level=.95, figsize=None):

        fig, axes = plt.subplots(len(params_), 1, squeeze=True, figsize=figsize)
        for i, param in enumerate(params_):
            samples = posterior_samples[param]
            # chain order is preserved in the posterior samples
            chained_samples = np.array_split(samples, mod.chains)
            # mean = np.mean(samples)
            # median = np.median(samples)
            # cred_min, cred_max = np.percentile(samples, 100 * (1 - ci_level)/2), \
            #                         np.percentile(samples, 100 * (1 + ci_level)/2)

            for k in range(mod.chains):
                axes[i].plot(chained_samples[k], lw=1, alpha=.5, label=f'chain {k+1}')
            axes[i].set_ylabel(param)
            # axes[i].legend()
            # draw horizontal lines
            # axes[i].axhline(mean, color=QualitativePalette['PostQ'].value[0], lw=2, alpha=.5, label='mean')
            # axes[i].axhline(median, color=QualitativePalette['PostQ'].value[1], lw=2, alpha=.5, label='median')
            # axes[i].axhline(cred_min, linestyle='--', color='k', alpha=.5, label='95% CI')
            # axes[i].axhline(cred_max, linestyle='--', color='k', alpha=.5)

        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper right', bbox_to_anchor=(1.15, 0.9))
        plt.suptitle('Trace of Posterior Samples')
        plt.xlabel('draw')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        return fig

    def _pair_plot(posterior_samples, pair_type='scatter', n_bins=20):
        samples_df = pd.DataFrame({key: posterior_samples[key].flatten() for key in params_})

        fig = sns.pairplot(samples_df, kind=pair_type, diag_kws=dict(bins=n_bins))
        fig.fig.suptitle("Pair Plot")
        fig.fig.tight_layout(rect=[0, 0.03, 1, 0.95])

        return fig

    if kind == 'density':
        fig = _density_plot(posterior_samples, n_bins=n_bins, ci_level=ci_level, figsize=figsize)
    elif kind == 'trace':
        fig = _trace_plot(posterior_samples, ci_level=ci_level, figsize=figsize)
    elif kind == 'pair':
        fig = _pair_plot(posterior_samples, pair_type=pair_type, n_bins=n_bins)

    if path:
        plt.savefig(path)

    return fig
