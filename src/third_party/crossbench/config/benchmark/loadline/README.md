# LoadLine Benchmark

This folder contains configs for the LoadLine benchmark. The goal of the
benchmark is to facilitate web performance optimization based on a realistic
workload. The benchmark has two workload variants:

*   General-purpose workload representative of the web usage on mobile phones
    ("phone");

*   Android Tablet web performance workload ("tablet").

## tl;dr: Running the Benchmark

Run "phone" workload:

```
./cb.py loadline-phone --browser <browser>
```

Run "tablet" workload:

```
./cb.py loadline-tablet --browser <browser>
```

The browser can be `android:chrome-canary`, `android:chrome-stable` etc. See
crossbench docs for the full list of options.

Results will be located in `results/latest/`. Notable files in this directory:

*   `loadline_benchmark_probe.csv`: Final score for the run
*   `trace_processor/loadline_benchmark_score.csv`: Breakdown of scores per
    page and repetition

## Benchmark Details

### Background

Web is one of the most important use cases on mobile devices. Page loading speed
represents a crucial part of user experience, and is not well covered by
existing benchmarks (Speedometer, Jetstream, MotionMark). Experiments show that
raw CPU performance does not always result in faster web loading speeds, since
it's a complex highly parallelized process that stresses a lot of browser and OS
components and their interactions. Hence the need for a dedicated web loading
benchmark that will enable us to compare devices, track improvements across OS
and browser releases.

### Workload

We aimed for two configurations:

*   **Representative mobile Web on Android usage (~5 pages)**

    Aimed at covering loading scenarios representative of real web workloads and
    user environments on Android mobile phones.

*   **Android Tablet web performance (~5 pages)**

    A set of larger desktop-class workloads intended for tablet/large screen
    devices running Android.

The biggest challenges we faced in achieving this goal were:

*   **Representativeness**: How do we determine a representative set of web
    sites given the humongous corpus of websites whose overall distribution is
    not thoroughly understood.
*   **Metrics** Existing page load metrics generalize well for O(millions) of
    page loads across a variety of sites, but are poor fit to judge performance
    of a specific site
*   **Noise**: The web evolves. To ensure the benchmark workloads stay
    consistent over time, we chose to use recorded & replayed workloads.
    However, page load is very complex and indeterministic so naive replays are
    often not consistent.

### Site Selection

We did a thorough analysis to ensure we select relevant and representative
sites. Our aspiration was to understand the distribution of the most important
CUJs and performance characteristics on the web and use this knowledge to elect
a small number of representative CUJs, such that their performance
characteristics maximize coverage of the distribution.

Practically, we evaluated ~50 prominent sites across a number of different
characteristics (dimensions) via trace-based analysis, cross-checking via field
data. We clustered similar pages and selected representatives for important
clusters. In the end, this was a manual selection aided by algorithmic
clustering/correlation analysis.

We looked at over 20 dimensions for suitability and relevance to our site
selection, and low correlation between dimensions. Of these, we chose 6 primary
metrics that we optimized coverage on: Website type, workload size (CPU time),
DOM/Layout complexity (#nodes), JavaScript heap size, time spent in V8, time
spent in V8 callbacks into Blink. Secondarily, we included utilization of web
features and relevant mojo interfaces, e.g. Video, cookies, main/subframe
communication, input events, frame production, network requests, etc.

In the end we selected 5 sites for each configuration which we plan to extend in
the future.

#### Mobile

| Page (mobile version)      | CUJ               | Performance characteristics |
| -------------------------- | ------------------ | -------------------------- |
| amazon.co.uk <br> (product page) | Shopping           | * average page load, large workload, large DOM/JS (but heavier on DOM) <br> * high on OOPIFs, input, http(s) resources, frame production |
| cnn.com <br> (article)           | News               | * slow page load, large workload, large DOM/JS (but heavier on JS) <br> * high on iframes, main frame, local storage, cookies, http(s) resources |
| wikipedia.org <br> (article)     | Reference work     | * fast page load, small workload, large DOM, small JS <br> * high on input <br> * low on iframes, http(s) resources, frame production |
| globo.com <br> (homepage)        | News / web portal  | * slow page load, large workload, small DOM, large JS <br> * high on iframes, OOPIFs, http(s) resources, frame production, cookies |
| google.com <br> (results)        | Search             | * fast page load, average workload, average DOM + JS <br> * high on main frame, local storage, video |

#### Tablet

| Page (desktop version)     | CUJ          | Performance characteristics      |
| -------------------------- | ------------ | -------------------------------- |
| amazon.co.uk <br> (product page) | Shopping     | * average page load, large workload, large DOM, average JS <br> * high on OOPIFs, http(s) resources, frame production |
| cnn.com <br> (article)           | News         | * slow page load, large workload, large DOM/JS (but heavier on JS) <br> * high on iframes, local storage, video, frame production, cookies |
| docs.google.com <br> (document)  | Productivity | * slow page load, large workload, large DOM + JS (heavier on JS) <br> * high on main frame <br> * high on font resources |
| google.com <br> (results)        | Search       | * fast page load, low workload, low DOM + JS <br> * high on main frame, local storage <br> * low on video |
| youtube.com<br> (video)         | Media        | * slow page load, very high workload, large DOM, small JS heap, average JS time <br> * high on video |

### Metrics

Measuring page load accurately in generic ways is difficult (e.g. some pages
require significant work after LCP to become "interactive") and inaccurate
metrics risk incorrect power/perf trade-off choices. Once we had a selection of
sites, we looked at each one of them and devised site-specific metrics that
better reflect when a page is ready to be interacted with.

## Reproducibility / Noise

Page load is a very complex process and is inherently noisy. There is a lot of
concurrent work happening in the browser and slight timing differences can have
big impact in the actual workload being executed and thus in the perceived load
speed.

We took various measures to try to reduce this variability, but there is still
room to improve and we plan to do this in the next versions of this benchmark.

### Score

We are still actively developing this benchmark and we will try our best to keep
the score as stable across changes as possible. We will update the benchmark's
minor version if we introduce changes that have a chance of affecting the score.
This version is reported in the benchmark output and should be quoted when
sharing scores.

### Cross-device Comparisons

Workload on two different devices will differ due to variance in application
tasks, such as the number of frames rendered during load, timers being executed
more frequently during load, etc.

It is important to stress that page load is a complex workload. As a result, if
we were to compare scores between two devices A and B, device A having 2x the
CPU speed compared to device B, then A's score will be less than 2x of B's
score. This is not an error or an artifact of the measurement, this is a result
of the adaptable nature of web loading (and / or potential effort of a browser
trying to get the best user experience from the resources available). The
benchmark score reflects the actual user-observable loading speed.

### Web Page Replay

To maintain reproducibility, the benchmark uses the
[web page replay](https://chromium.googlesource.com/catapult/+/HEAD/web_page_replay_go/README.md)
mechanism. Archives of the web pages are stored in the
`chrome-partner-telemetry` cloud bucket, so you'll need access to that bucket to
run the benchmark on recorded pages (you can still run the benchmark on live
sites if you don't have the access, but there's no guarantee that results will
be reproducible/comparable).

### Repetitions {#repetitions}

By default, the benchmark runs **100** repetitions, as we have found that this
brings the noise to an acceptable level. You can override this setting via
`--repetitions`

### Thermal Throttling

Given the high number of repetitions in the standard configuration, thermal
throttling can be an issue, especially in more thermally constricted devices. A
one size fits all solution to this problem is quite hard; even detecting this is
very device specific. So for the first version of the benchmark, we leave it up
to the user to determine if the results of the benchmark might be influenced by
thermal issues. Crossbench has a way of adding a delay between repetitions that
can be used to mitigate this problem (at the expense of longer running times):
`--cool-down-time`.

In the future, we want to look at ways to aid users in detecting / mitigating
thermal throttling (e.g. notify users that thermal throttling happened during
the test or automatically waiting between repetitions until the device is in a
good thermal state).

## Configuration

In its standard configuration, the benchmark will run 100 iterations. In
addition, the WPR server will run on device, rather than on the host, to reduce
the noise caused by the latency introduced by the host to device connection.

Both these settings can be overridden if needed / desirable.
([Repetitions](#repetitions), [WPR on host](#host_wpr))

### Run the benchmark on live sites

```
./cb.py loadline-phone --browser <browser> --network live
```

*Attention:* This benchmark uses various custom metrics tailored to the
individual pages. If the pages change, it is not guaranteed that these metrics
will keep working.

### Record a new WPR archive

Uncomment the `wpr: {},` line in the probe config and run the benchmark on live
sites (see the command above). The archive will be located in
`results/latest/archive.wprgo`.

*Attention:* This benchmark uses various custom metrics tailored to the
individual pages. If the pages change, it is not guaranteed that these metrics
will keep working.

### Running WPR on the host {#host_wpr}

If you care about running as little overhead as possible on the device, e.g. for
power measurements, you might consider running the WPR server on the host
machine instead of the device under test. You can do this by

Adding `run_on_device: false,` to the corresponding network config file
`config/benchmark/loadline/network_config_phone.hjson` or
`config/benchmark/loadline/network_config_tablet.hjson`.

Note golang must be available on the host machine. Check
[go.mod](https://chromium.googlesource.com/catapult/+/HEAD/web_page_replay_go/go.mod)
for the minimum version.

### Run the benchmark with full set of experimental metrics

Sometimes to investigate a source of a regression, or get deeper insights,
it may be useful to collect more detailed traces and compute additional metrics.
This can be done with the following command:

```
./cb.py loadline-phone --browser <browser>\
  --probe-config config/benchmark/loadline/probe_config_experimental.hjson
```

Note that collecting detailed traces incurs significant overhead, so the
benchmark scores will likely be lower than in the default configuration.

## Common issues

### Problems finding wpr.go

If you see a `Could not find wpr.go binary` error:

*   If you have chromium checked out locally: set `CHROMIUM_SRC` environment
    variable to the path of your chromium/src folder.
*   If not (or if you're still getting this error): see the next section.

### Running the benchmark without full chromium checkout

Follow the
[crossbench development instructions](https://chromium.googlesource.com/crossbench/#development)
to check out code and run crossbench standalone.

### Problems accessing the cloud bucket

In some cases, you might need to download the web page archive manually. In this
case, save the archive file corresponding to the version you are running
(`gs://chrome-partner-telemetry/loading_benchmark/archive_*.wprgo`) locally and
run the benchmark as follows:

```
./cb.py loadline-phone --network <path to archive.wprgo>
```
