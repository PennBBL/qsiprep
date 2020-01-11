# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Utility workflows
^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_reference_wf
.. autofunction:: init_enhance_and_skullstrip_dwi_wf

"""
import os
from pathlib import Path
import nibabel as nb

from nipype.pipeline import engine as pe
from nipype.utils.filemanip import split_filename
from nipype.interfaces import utility as niu, fsl, afni
from ...niworkflows.interfaces import SimpleBeforeAfter
from ...niworkflows.interfaces.utils import CopyHeader
from ...engine import Workflow
from ...interfaces.nilearn import Merge
from ...interfaces.dsi_studio import DSIStudioSrcQC, DSIStudioCreateSrc


DEFAULT_MEMORY_MIN_GB = 0.01


def init_modelfree_qc_wf(dwi_files=None, name='dwi_qc_wf'):
    """
    This workflow runs DSI Studio's QC metrics

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from qsiprep.workflows.dwi.util import init_dwi_reference_wf
        wf = init_dwi_reference_wf(omp_nthreads=1)

    **Parameters**

        dwi_files : list of DWI Files
            A b=0 image
        name : str
            Name of workflow (default: ``dwi_qc_wf``)

    **Inputs**
        dwi_file
            a single 4D dwi series
        bval_file
            bval file corresponding to the concatenated dwi_files inputs or dwi_file
        bvec_file
            bvec file corresponding to the concatenated dwi_files inputs or dwi_file

    **Outputs**

        qc file
            DSI Studio's src QC metrics for the input data


    """
    workflow = Workflow(name=name)
    workflow.__desc__ = """\
"""
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['dwi_file', 'bval_file', 'bvec_file']),
        name='inputnode')
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['qc_file']),
        name='outputnode')

    raw_src = pe.Node(DSIStudioCreateSrc(), name='raw_src')
    raw_qc = pe.Node(DSIStudioSrcQC(), name='raw_qc')

    if dwi_files:
        if len(dwi_files) > 1:
            concat_raw_dwis = pe.Node(Merge(in_files=dwi_files, is_dwi=True),
                                      name='concat_raw_dwis')
            workflow.connect(concat_raw_dwis, "out_file", raw_src, "input_nifti_file")
        else:
            raw_src.inputs.input_nifti_file = dwi_files[0]
    else:
        workflow.connect(inputnode, 'dwi_file', raw_src, 'input_nifti_file')

    workflow.connect([
        (inputnode, raw_src, [
            ('out_bval', 'input_bvals'),
            ('out_bvec', 'input_bvecs')]),
        (raw_src, raw_qc, [('output_src', 'src_file')]),
        (raw_qc, outputnode, [('qc_txt', 'qc_summary')])
    ])

    return workflow
