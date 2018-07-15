Frequently Asked Questions
==========================

What kind of data can I upload to Qiita for processing?
-------------------------------------------------------

We need 3 things: raw data, sample template, and prep template. At this
moment, raw data is fastq files without demultiplexing with forward,
reverse (optional) and barcode reads. We should have before the end of
the week SFF processing so it's OK to upload. Note that we are accepting
any kind of target gene (16S, 18S, ITS, whatever) as long as they have
some kind of demultiplexing strategy and that you can also upload WGS.
However, WGS processing is not ready.

What's the difference between a sample and a prep template?
-----------------------------------------------------------

Sample template is the information about your samples, including
environmental and other important information about them. The prep
template is basically what kind of wet lab work all or a subset of the
samples had. If you collected 100 samples, you are going to need 100
rows in your sample template describing each of them, this includes
blanks, etc. Then you prepared 95 of them for 16S and 50 of them for
18S. Thus, you are going to need 2 prep templates: one with 95 rows
describing the preparation for 16S, and another one with 50 to
describing the 18S. For a more complex example go
`here <#h.eddzjlm5e6l6>`__ and for examples of these files you can go to
the "Upload instructions"
`here <https://www.google.com/url?q=https%3A%2F%2Fvamps.mbl.edu%2Fmobe_workshop%2Fwiki%2Findex.php%2FMain_Page&sa=D&sntz=1&usg=AFQjCNE4PTOKIvFNlWtHmJyLLy11mfzF8A>`__.

.. _example_study_processing_workflow:

Example study processing workflow
---------------------------------

A few more instructions: for the example above the workflow should be:

#. Create a new study
#. Add a sample template, you can add 1, try to process it and the
   system will let you know if you have errors or missing columns. The
   most common errors are: the sample name column should be named
<<<<<<< HEAD
   sample\_name, duplicated sample names are not permitted, and the prep
   template should contain all the samples in the sample template or a
   subset. Finally, if you haven't processed your sample templates and
   can add a column to your template named sloan\_status with this info:
   SLOAN (funded by Sloan), SLOAN\_COMPATIBLE (not Sloan funded but with
   compatible metadata, usually public), NOT\_SLOAN (not included i.e.
   private study), that will be great!
#. Add a raw data. Depending on your barcoding/sequencing strategy you
   might need 1 or 2 raw datas for the example above. If you have two
   different fastq file sets (forward, reverse (optional) and barcodes)
   you will need two raw datas but if you only have one set, you only
   need one.
#. You can link your raw data to your files
#. You can add a prep template to your raw data. If you have the case
   with only one fastq set (forward, reverse (optional) and barcodes),
   you can add 2 different prep templates. Common missing fields here
   are: emp\_status, center\_name, run\_prefix, platform,
   library\_construction\_protocol, experiment\_design\_description,
   center\_project\_name. Note that if you get a 500 error at this stage
   is highly probable because emp\_status only accepts 3 values: 'EMP',
   'EMP\_Processed', 'NOT\_EMP', if errors persist please do not
   hesitate to contact us.
#. You can preprocess your files. For target gene, this means
   demultiplexing and QC.

=======
   sample\_name, duplicated sample names are not permitted. For a full list of
   required fields, visit :doc:`gettingstartedguide/index`.
#. **Add a prep information file to your study for each data type.** The prep
   information file should contain all the samples in the sample information
   file or a subset. If you have more than one FASTQ file set (forward,
   reverse (optional) and barcodes) you will need to add a run_prefix column,
   see :ref:`prepare_information_files`.
   A prep information file and a QIIME compatible mapping file will
   be available for download after the prep information file is added
   successfully.
#. **Upload and link your raw data to each of your prep information files.**
   Depending on your barcoding/sequencing strategy you might need 1 or more
   raw data file sets. If you have 2 raw data sets you may have to rename one
   set so that each set has a different name. If they have the same name they
   will over-write on upload. Note that you can have one FASTQ file set linked
   to more than one prep information file.
#. **Preprocess your files.** For target gene amplicon sequencing, this will demux
   and QC. There are multiple options for preprocessing depending on the
   barcode format and the data output from the sequencing center - this may
   require a series of trial and error to establish the correct option for
   your data files. After demultiplexing a log file is generated with
   statistics about the files demultiplexed including the number of sequences
   assigned per sample.
#. **Process each of your preprocessed data types.** For target gene, this will
   perform closed OTU picking against the latest version of Greengenes and can
   be quite time consuming depending on the number of samples and the depth
   of sequencing.

.. _issues_unzip:

How to solve unzip errors?
--------------------------

When downloading large zip files within Qiita there is a change that you will get
an error like: **"start of central directory not found; zipfile corrupt"**. This issue
arises from using old versions of zip and you need to have unzip >= 6.0.0. To check
you unzip version you can run: `unzip -v`.

To update your unzip for most operating systems you can simply use your regular package
admin program. However, for Mac we suggest using
`this version of unzip <ftp://ftp.microbio.me/pub/qiita/unzip>`__.

How to solve BIOM name errors?
------------------------------

When uploading a BIOM table, you may get an error like: **"The sample ids in the BIOM
table do not match the ones in the prep information. Please, provide the column "run_prefix"
in the prep information to map the existing sample ids to the prep information sample ids."**.
This issue arises if your sample names in your BIOM table do not match with the sample names
in your preparation information file.

To correct this issue, simply add a column to your preparation information file named
"run_prefix". In this column, add the sample names from your BIOM table that matches the sample
names listed in the sample_name column in your preparation information file.
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed
