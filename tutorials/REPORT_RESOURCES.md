# Report resource limits

The interactive command reads accepted core reports and packages their linked
evidence into HTML. It does not submit an allocation or rerun trajectory
analysis. Its cost depends on the report count, figures, structures, linked
assets, and build options, not just the raw trajectory's frame count.

The core campaign's CPU, memory, and time ceilings do not cover this separate
build. Core final reporting and the companion HTML build are different stages.
There is currently no calibrated viewer resource recommendation. Do not reuse
the core finalizer's one-CPU, 2-GiB, 30-minute defaults as a viewer estimate, or
assume that reading reports makes a build safe on a login node.

For an unmeasured cluster build, obtain an approved compute allocation or copy
the accepted campaign and its linked evidence to a suitable workstation. Use
the same recorded viewer environment. Login-node execution requires site
permission for a measured workload. On a workstation, allow enough free memory
and storage for both the source evidence and the packaged report.

Record elapsed time, peak resident memory, output size, source report counts,
options, and package revisions for representative builds. Use the site's job
accounting or system measurement tools, then choose headroom under local
policy. A small NEMO build does not calibrate a larger campaign. If a build
fails, preserve its logs and partial output; use a new `--output-name` after
resolving the cause rather than overwriting evidence.

Build only after the core completion checks pass. Keep the prepared directory
selected during recovery: the NEMO tutorials call it `NEMO_ANALYSIS`. Transfer
the whole `interactive-report/` directory after building, including its linked
evidence. Optional molecular-panel rendering is another workload and needs its
own resource check.
