"""
Seed sample data for demo / marker accounts.

Creates:
- Realistic research projects with well-known peer-reviewed papers,
  full bibliographic metadata, summaries, citations in mixed styles,
  and comparison tables
Usage:
    python manage.py seed_sample_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

from researchapp.models import (
    UserDetail, Subscription, ResearchProject, Resource,
    ResearchSummary, Citation,
    ComparisonTable, ComparisonColumn, ComparisonRow, ComparisonCell,
)
from researchapp.citations import format_citation


PROJECTS_DATA = [
    {
        'title': 'Transformer Architectures and Foundation Models',
        'description': (
            'Literature review of seminal papers that defined modern '
            'Transformer-based foundation models from the original 2017 '
            '"Attention Is All You Need" paper through BERT, GPT-3, and the '
            'instruction-tuned chat models that followed.'
        ),
        'resources': [
            {
                'title': 'Attention Is All You Need',
                'type': 'paper',
                'description': (
                    'Introduces the Transformer architecture, replacing recurrence '
                    'with multi-head self-attention and parallelisable training.'
                ),
                'authors': 'Vaswani, A.; Shazeer, N.; Parmar, N.; Uszkoreit, J.; Jones, L.; Gomez, A. N.; Kaiser, L.; Polosukhin, I.',
                'year': '2017',
                'venue': 'Advances in Neural Information Processing Systems (NeurIPS)',
                'volume': '30',
                'pages': '5998-6008',
                'doi': '10.48550/arXiv.1706.03762',
                'url': 'https://arxiv.org/abs/1706.03762',
                'extracted_text': (
                    'The dominant sequence transduction models are based on complex recurrent '
                    'or convolutional neural networks that include an encoder and a decoder. '
                    'We propose a new simple network architecture, the Transformer, based '
                    'solely on attention mechanisms, dispensing with recurrence and '
                    'convolutions entirely. Experiments on two machine translation tasks show '
                    'these models to be superior in quality while being more parallelisable '
                    'and requiring significantly less time to train.'
                ),
            },
            {
                'title': 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
                'type': 'paper',
                'description': (
                    'Introduces masked language modelling and next-sentence prediction '
                    'as pre-training objectives, achieving SOTA across 11 NLP tasks.'
                ),
                'authors': 'Devlin, J.; Chang, M.-W.; Lee, K.; Toutanova, K.',
                'year': '2019',
                'venue': 'Proceedings of NAACL-HLT',
                'pages': '4171-4186',
                'doi': '10.18653/v1/N19-1423',
                'url': 'https://arxiv.org/abs/1810.04805',
                'extracted_text': (
                    'We introduce a new language representation model called BERT, which '
                    'stands for Bidirectional Encoder Representations from Transformers. '
                    'Unlike recent language representation models, BERT is designed to pre-train '
                    'deep bidirectional representations from unlabeled text by jointly '
                    'conditioning on both left and right context in all layers. BERT obtains '
                    'new state-of-the-art results on eleven natural language processing tasks.'
                ),
            },
            {
                'title': 'Language Models are Few-Shot Learners (GPT-3)',
                'type': 'paper',
                'description': (
                    'Demonstrates that scaling autoregressive language models to 175B '
                    'parameters yields strong few-shot in-context learning.'
                ),
                'authors': 'Brown, T. B.; Mann, B.; Ryder, N.; Subbiah, M.; Kaplan, J.; Dhariwal, P.; Neelakantan, A.; Shyam, P.; Sastry, G.; Askell, A.; Agarwal, S.; Herbert-Voss, A.; Krueger, G.; Henighan, T.; Child, R.; Ramesh, A.; Ziegler, D. M.; Wu, J.; Winter, C.; Hesse, C.; Chen, M.; Sigler, E.; Litwin, M.; Gray, S.; Chess, B.; Clark, J.; Berner, C.; McCandlish, S.; Radford, A.; Sutskever, I.; Amodei, D.',
                'year': '2020',
                'venue': 'Advances in Neural Information Processing Systems (NeurIPS)',
                'volume': '33',
                'pages': '1877-1901',
                'doi': '10.48550/arXiv.2005.14165',
                'url': 'https://arxiv.org/abs/2005.14165',
                'extracted_text': (
                    'Recent work has demonstrated substantial gains on many NLP tasks and '
                    'benchmarks by pre-training on a large corpus of text followed by '
                    'fine-tuning on a specific task. We show that scaling up language models '
                    'greatly improves task-agnostic, few-shot performance, sometimes even '
                    'reaching competitiveness with prior state-of-the-art fine-tuning '
                    'approaches. Specifically, we train GPT-3, an autoregressive language '
                    'model with 175 billion parameters.'
                ),
            },
            {
                'title': 'Training language models to follow instructions with human feedback (InstructGPT)',
                'type': 'paper',
                'description': (
                    'Introduces RLHF as an alignment technique, producing models that are '
                    'preferred by labellers despite having far fewer parameters than GPT-3.'
                ),
                'authors': 'Ouyang, L.; Wu, J.; Jiang, X.; Almeida, D.; Wainwright, C. L.; Mishkin, P.; Zhang, C.; Agarwal, S.; Slama, K.; Ray, A.; Schulman, J.; Hilton, J.; Kelton, F.; Miller, L.; Simens, M.; Askell, A.; Welinder, P.; Christiano, P.; Leike, J.; Lowe, R.',
                'year': '2022',
                'venue': 'Advances in Neural Information Processing Systems (NeurIPS)',
                'volume': '35',
                'doi': '10.48550/arXiv.2203.02155',
                'url': 'https://arxiv.org/abs/2203.02155',
                'extracted_text': (
                    'Making language models bigger does not inherently make them better at '
                    'following a user\'s intent. We show an avenue for aligning language '
                    'models with user intent on a wide range of tasks by fine-tuning with '
                    'human feedback. In human evaluations, outputs from the 1.3B-parameter '
                    'InstructGPT model are preferred to outputs from the 175B GPT-3, despite '
                    'having 100x fewer parameters.'
                ),
            },
        ],
        'summaries': [
            {
                'title': 'From Attention to Alignment: a 5-year Arc',
                'content': (
                    '**Overview**\n'
                    'Between 2017 and 2022 the Transformer evolved from a translation '
                    'architecture into the substrate of all general-purpose language models. '
                    'Three steps mattered most: the original architecture, scaling, and '
                    'alignment via human feedback.\n\n'
                    '**Key Findings**\n'
                    '- The Transformer removed recurrence/convolution entirely and produced '
                    'a parallelisable training graph that scaled almost linearly with hardware.\n'
                    '- BERT showed bidirectional pre-training plus task-specific fine-tuning '
                    'lifts state-of-the-art across an unusually broad range of NLP tasks.\n'
                    '- GPT-3 demonstrated that scaling autoregressive LMs to 175B parameters '
                    'enables few-shot in-context learning without gradient updates.\n'
                    '- InstructGPT showed that a 1.3B model aligned with RLHF can beat a 175B '
                    'base model on user-preference evaluations.\n\n'
                    '**Methodology**\n'
                    'All four papers use Transformer-based architectures; the divergence is in '
                    'objectives (MLM, autoregressive, supervised, RLHF) and scale.\n\n'
                    '**Implications**\n'
                    'Capability does not come from architecture alone it requires the right '
                    'pre-training objective, scale, and post-training alignment.'
                ),
                'cite_indices': [0, 1, 2, 3],
                'styles': ['ieee', 'apa', 'apa', 'mla'],
            },
        ],
        'comparisons': [
            {
                'title': 'Foundation Model Generations',
                'columns': ['Criterion', 'Transformer (2017)', 'BERT (2019)', 'GPT-3 (2020)', 'InstructGPT (2022)'],
                'rows': ['Objective', 'Parameters', 'Strength', 'Limitation'],
                'cells': [
                    ['Seq2seq translation', 'Masked LM + NSP', 'Autoregressive LM', 'Supervised + RLHF'],
                    ['65M (base)', '110M / 340M', '175B', '1.3B / 6B / 175B'],
                    ['Parallel training', 'Transfer to many tasks', 'Few-shot learning', 'Preferred outputs'],
                    ['Specialised', 'Needs fine-tuning', 'Hallucination, refusal', 'Distillation cost'],
                ],
            },
        ],
    },
    {
        'title': 'Protein Structure Prediction with Deep Learning',
        'description': (
            'Comparative review of AlphaFold 2, RoseTTAFold, and ESMFold '
            'covering the architectural innovations behind the protein structure '
            'breakthrough recognised by the 2024 Nobel Prize in Chemistry.'
        ),
        'resources': [
            {
                'title': 'Highly accurate protein structure prediction with AlphaFold',
                'type': 'paper',
                'description': (
                    'AlphaFold 2 achieves near-experimental accuracy on CASP14 using '
                    'an Evoformer/structure module pipeline informed by MSAs and pair '
                    'representations.'
                ),
                'authors': 'Jumper, J.; Evans, R.; Pritzel, A.; Green, T.; Figurnov, M.; Ronneberger, O.; Tunyasuvunakool, K.; Bates, R.; Žídek, A.; Potapenko, A.; Bridgland, A.; Meyer, C.; Kohl, S. A. A.; Ballard, A. J.; Cowie, A.; Romera-Paredes, B.; Nikolov, S.; Jain, R.; Adler, J.; Back, T.; Petersen, S.; Reiman, D.; Clancy, E.; Zielinski, M.; Steinegger, M.; Pacholska, M.; Berghammer, T.; Bodenstein, S.; Silver, D.; Vinyals, O.; Senior, A. W.; Kavukcuoglu, K.; Kohli, P.; Hassabis, D.',
                'year': '2021',
                'venue': 'Nature',
                'volume': '596',
                'pages': '583-589',
                'doi': '10.1038/s41586-021-03819-2',
                'url': 'https://www.nature.com/articles/s41586-021-03819-2',
                'extracted_text': (
                    'Proteins are essential to life, and understanding their structure can '
                    'facilitate a mechanistic understanding of their function. We present a '
                    'computational method, AlphaFold, that can predict protein structures with '
                    'atomic accuracy even where no similar structure is known. The neural '
                    'network is based on attention-based mechanisms operating on multiple '
                    'sequence alignments and pairwise representations.'
                ),
            },
            {
                'title': 'Accurate prediction of protein structures and interactions using a three-track neural network (RoseTTAFold)',
                'type': 'paper',
                'description': (
                    'Independent open-source approach using a three-track architecture; '
                    'less accurate than AlphaFold 2 but trained with fewer compute resources.'
                ),
                'authors': 'Baek, M.; DiMaio, F.; Anishchenko, I.; Dauparas, J.; Ovchinnikov, S.; Lee, G. R.; Wang, J.; Cong, Q.; Kinch, L. N.; Schaeffer, R. D.; Millán, C.; Park, H.; Adams, C.; Glassman, C. R.; DeGiovanni, A.; Pereira, J. H.; Rodrigues, A. V.; van Dijk, A. A.; Ebrecht, A. C.; Opperman, D. J.; Sagmeister, T.; Buhlheller, C.; Pavkov-Keller, T.; Rathinaswamy, M. K.; Dalwadi, U.; Yip, C. K.; Burke, J. E.; Garcia, K. C.; Grishin, N. V.; Adams, P. D.; Read, R. J.; Baker, D.',
                'year': '2021',
                'venue': 'Science',
                'volume': '373',
                'issue': '6557',
                'pages': '871-876',
                'doi': '10.1126/science.abj8754',
                'url': 'https://www.science.org/doi/10.1126/science.abj8754',
                'extracted_text': (
                    'DeepMind\'s AlphaFold 2 has demonstrated remarkable success in protein '
                    'structure prediction. Here, we present RoseTTAFold, a three-track network '
                    'that simultaneously processes 1D sequence information, 2D distance maps, '
                    'and 3D coordinates. RoseTTAFold approaches the accuracy of AlphaFold 2 '
                    'while requiring substantially less computational resources for training.'
                ),
            },
            {
                'title': 'Evolutionary-scale prediction of atomic-level protein structure (ESMFold)',
                'type': 'paper',
                'description': (
                    'ESMFold removes the MSA dependency by using a large protein language '
                    'model, enabling order-of-magnitude faster inference.'
                ),
                'authors': 'Lin, Z.; Akin, H.; Rao, R.; Hie, B.; Zhu, Z.; Lu, W.; Smetanin, N.; Verkuil, R.; Kabeli, O.; Shmueli, Y.; dos Santos Costa, A.; Fazel-Zarandi, M.; Sercu, T.; Candido, S.; Rives, A.',
                'year': '2023',
                'venue': 'Science',
                'volume': '379',
                'issue': '6637',
                'pages': '1123-1130',
                'doi': '10.1126/science.ade2574',
                'url': 'https://www.science.org/doi/10.1126/science.ade2574',
                'extracted_text': (
                    'Recent advances in machine learning have leveraged evolutionary information '
                    'in multiple sequence alignments to predict protein structure. We demonstrate '
                    'that protein language models trained at scale enable atomic-resolution '
                    'structure prediction directly from individual protein sequences, achieving '
                    'an order-of-magnitude speed-up over MSA-based methods.'
                ),
            },
            {
                'title': 'AlphaFold Protein Structure Database',
                'type': 'link',
                'url': 'https://alphafold.ebi.ac.uk/',
                'description': (
                    'EMBL-EBI database providing predicted structures for over 200 million '
                    'proteins covering essentially every catalogued organism.'
                ),
                'authors': 'Varadi, M.; Anyango, S.; Deshpande, M.; Nair, S.; Natassia, C.; Yordanova, G.; Yuan, D.; Stroe, O.; Wood, G.; Laydon, A.; Žídek, A.; Green, T.; Tunyasuvunakool, K.; Petersen, S.; Jumper, J.; Clancy, E.; Green, R.; Vora, A.; Lutfi, M.; Figurnov, M.; Cowie, A.; Hobbs, N.; Kohli, P.; Kleywegt, G.; Birney, E.; Hassabis, D.; Velankar, S.',
                'year': '2022',
                'venue': 'Nucleic Acids Research',
                'volume': '50',
                'issue': 'D1',
                'pages': 'D439-D444',
                'doi': '10.1093/nar/gkab1061',
                'extracted_text': (
                    'The AlphaFold Protein Structure Database provides open access to high-quality '
                    'predicted protein structures, enabling researchers to integrate computationally '
                    'predicted structures into their experimental workflows.'
                ),
            },
        ],
        'summaries': [
            {
                'title': 'Three approaches to the protein folding problem',
                'content': (
                    '**Overview**\n'
                    'Deep learning has effectively solved the protein folding problem for '
                    'soluble single-chain proteins. Three architectures dominate the literature: '
                    'AlphaFold 2 (Evoformer + structure module), RoseTTAFold (three-track '
                    'attention), and ESMFold (language-model-only).\n\n'
                    '**Key Findings**\n'
                    '- AlphaFold 2 set the benchmark on CASP14 with median GDT-TS ~92, '
                    'comparable to experimental resolution.\n'
                    '- RoseTTAFold is open-source and produces high-quality predictions with '
                    'considerably less compute, enabling academic labs to iterate.\n'
                    '- ESMFold eliminates the MSA step by relying on a 15B-parameter protein '
                    'language model, trading some accuracy for ~60× faster inference.\n'
                    '- The AlphaFold DB has scaled to >200 million predictions, reshaping how '
                    'biologists design experiments.\n\n'
                    '**Implications**\n'
                    'Future work focuses on protein complexes, dynamics, and structure-guided '
                    'design of binders and enzymes.'
                ),
                'cite_indices': [0, 1, 2, 3],
                'styles': ['apa', 'ieee', 'apa', 'harvard'],
            },
        ],
        'comparisons': [
            {
                'title': 'Protein Structure Predictors',
                'columns': ['Criterion', 'AlphaFold 2', 'RoseTTAFold', 'ESMFold'],
                'rows': ['Architecture', 'MSA required', 'Speed (relative)', 'Accuracy (CASP)'],
                'cells': [
                    ['Evoformer + IPA', 'Three-track', 'ESM-2 + folding trunk'],
                    ['Yes', 'Yes', 'No'],
                    ['1×', '2×', '60×'],
                    ['Highest', 'High', 'Moderate-High'],
                ],
            },
        ],
    },
    {
        'title': 'CRISPR-Cas Genome Editing: Foundations & Therapeutics',
        'description': (
            'Tracks the CRISPR-Cas9 system from the 2012 mechanistic paper through '
            'the first FDA-approved CRISPR therapy (Casgevy) in 2023.'
        ),
        'resources': [
            {
                'title': 'A Programmable Dual-RNA-Guided DNA Endonuclease in Adaptive Bacterial Immunity',
                'type': 'paper',
                'description': (
                    'The foundational paper establishing Cas9 as a programmable, '
                    'sequence-specific DNA endonuclease guided by a dual-RNA work '
                    'recognised by the 2020 Nobel Prize in Chemistry.'
                ),
                'authors': 'Jinek, M.; Chylinski, K.; Fonfara, I.; Hauer, M.; Doudna, J. A.; Charpentier, E.',
                'year': '2012',
                'venue': 'Science',
                'volume': '337',
                'issue': '6096',
                'pages': '816-821',
                'doi': '10.1126/science.1225829',
                'url': 'https://www.science.org/doi/10.1126/science.1225829',
                'extracted_text': (
                    'Clustered regularly interspaced short palindromic repeats (CRISPR)/CRISPR-'
                    'associated (Cas) systems provide bacteria and archaea with adaptive immunity '
                    'against viruses and plasmids by using CRISPR RNAs (crRNAs) to guide the '
                    'silencing of invading nucleic acids. We show that in a subset of these '
                    'systems, the mature crRNA forms a dual-RNA structure with a transactivating '
                    'tracrRNA that directs the Cas9 protein to introduce double-stranded breaks '
                    'in target DNA. Our study reveals a family of endonucleases that use dual-RNAs '
                    'for site-specific DNA cleavage and highlights the potential to exploit the '
                    'system for RNA-programmable genome editing.'
                ),
            },
            {
                'title': 'Multiplex Genome Engineering Using CRISPR/Cas Systems',
                'type': 'paper',
                'description': (
                    'First demonstration of CRISPR-Cas9 editing in mammalian cells, '
                    'including multiplexed simultaneous edits.'
                ),
                'authors': 'Cong, L.; Ran, F. A.; Cox, D.; Lin, S.; Barretto, R.; Habib, N.; Hsu, P. D.; Wu, X.; Jiang, W.; Marraffini, L. A.; Zhang, F.',
                'year': '2013',
                'venue': 'Science',
                'volume': '339',
                'issue': '6121',
                'pages': '819-823',
                'doi': '10.1126/science.1231143',
                'url': 'https://www.science.org/doi/10.1126/science.1231143',
                'extracted_text': (
                    'Functional elucidation of causal genetic variants and elements requires '
                    'precise genome editing technologies. We engineered two different type II '
                    'CRISPR/Cas systems and demonstrate that Cas9 nucleases can be directed by '
                    'short RNAs to induce precise cleavage at endogenous genomic loci in human '
                    'and mouse cells. Cas9 can be converted into a nicking enzyme to facilitate '
                    'homology-directed repair with minimal mutagenic activity.'
                ),
            },
            {
                'title': 'CRISPR-Cas9 Gene Editing for Sickle Cell Disease and Beta-Thalassemia (CTX001/Casgevy)',
                'type': 'paper',
                'description': (
                    'Clinical results that supported FDA approval of Casgevy, the first '
                    'CRISPR-based gene therapy.'
                ),
                'authors': 'Frangoul, H.; Altshuler, D.; Cappellini, M. D.; Chen, Y.-S.; Domm, J.; Eustace, B. K.; Foell, J.; de la Fuente, J.; Grupp, S.; Handgretinger, R.; Ho, T. W.; Kattamis, A.; Kernytsky, A.; Lekstrom-Himes, J.; Li, A. M.; Locatelli, F.; Mapara, M. Y.; de Montalembert, M.; Rondelli, D.; Sharma, A.; Sheth, S.; Soni, S.; Steinberg, M. H.; Wall, D.; Yen, A.; Corbacioglu, S.',
                'year': '2021',
                'venue': 'New England Journal of Medicine',
                'volume': '384',
                'issue': '3',
                'pages': '252-260',
                'doi': '10.1056/NEJMoa2031054',
                'url': 'https://www.nejm.org/doi/10.1056/NEJMoa2031054',
                'extracted_text': (
                    'Transfusion-dependent β-thalassemia and sickle cell disease are severe '
                    'monogenic diseases with severe and potentially life-threatening manifestations. '
                    'We show that CRISPR-Cas9 editing of BCL11A in autologous hematopoietic stem '
                    'and progenitor cells reactivates fetal hemoglobin synthesis and produces '
                    'pancellular distribution of HbF, with both patients becoming transfusion-'
                    'independent after a single infusion.'
                ),
            },
            {
                'title': 'FDA Approves First Gene Therapies to Treat Patients with Sickle Cell Disease',
                'type': 'link',
                'url': 'https://www.fda.gov/news-events/press-announcements/fda-approves-first-gene-therapies-treat-patients-sickle-cell-disease',
                'description': (
                    'Official FDA press release announcing approval of Casgevy and Lyfgenia '
                    'on 8 December 2023.'
                ),
                'authors': 'U.S. Food and Drug Administration',
                'year': '2023',
                'venue': 'FDA News',
                'extracted_text': (
                    'The U.S. Food and Drug Administration today approved two milestone treatments, '
                    'Casgevy and Lyfgenia, representing the first cell-based gene therapies for the '
                    'treatment of sickle cell disease in patients 12 years and older. Casgevy is the '
                    'first FDA-approved treatment to use CRISPR/Cas9, a genome editing technology.'
                ),
            },
        ],
        'summaries': [
            {
                'title': 'From RNA-guided endonuclease to FDA approval in eleven years',
                'content': (
                    '**Overview**\n'
                    'CRISPR-Cas9 moved from bacterial immunity discovery to an FDA-approved '
                    'human therapy in just over a decade. Three milestones anchor the timeline: '
                    'the 2012 mechanism paper, the 2013 mammalian-cell demonstration, and the '
                    '2023 Casgevy approval for sickle cell disease.\n\n'
                    '**Key Findings**\n'
                    '- The dual-RNA Cas9 mechanism is programmable simply by changing the spacer '
                    'sequence, making site-specific cleavage trivial relative to ZFN/TALEN tools.\n'
                    '- Within one year of the mechanism paper, multiplex editing in human and '
                    'mouse cells was demonstrated.\n'
                    '- The first approved CRISPR therapy edits BCL11A in autologous HSPCs to '
                    'reactivate fetal hemoglobin, eliminating vaso-occlusive crises in trial '
                    'patients.\n\n'
                    '**Limitations**\n'
                    'Off-target editing, large-fragment repair efficiency, and delivery to '
                    'tissues other than HSPCs remain active research areas.'
                ),
                'cite_indices': [0, 1, 2, 3],
                'styles': ['apa', 'mla', 'apa', 'chicago'],
            },
        ],
        'comparisons': [
            {
                'title': 'CRISPR Editing Milestones',
                'columns': ['Year', '2012', '2013', '2023'],
                'rows': ['Contribution', 'Authors', 'Venue', 'Impact'],
                'cells': [
                    ['Cas9 mechanism', 'Mammalian editing', 'First FDA approval'],
                    ['Jinek, Doudna, Charpentier', 'Cong, Zhang', 'Frangoul et al.'],
                    ['Science', 'Science', 'NEJM / FDA'],
                    ['Nobel 2020', 'Clinical pipeline', 'Casgevy launched'],
                ],
            },
        ],
    },
    {
        'title': 'Privacy-Preserving Machine Learning at Scale',
        'description': (
            'Comparative review of federated learning, differential privacy, and '
            'fully homomorphic encryption as deployed in production systems.'
        ),
        'resources': [
            {
                'title': 'Communication-Efficient Learning of Deep Networks from Decentralized Data (FedAvg)',
                'type': 'paper',
                'description': (
                    'Introduces FedAvg, the canonical federated learning algorithm, and '
                    'demonstrates feasibility on mobile keyboards.'
                ),
                'authors': 'McMahan, H. B.; Moore, E.; Ramage, D.; Hampson, S.; y Arcas, B. A.',
                'year': '2017',
                'venue': 'Proceedings of the 20th International Conference on Artificial Intelligence and Statistics (AISTATS)',
                'pages': '1273-1282',
                'doi': '10.48550/arXiv.1602.05629',
                'url': 'https://arxiv.org/abs/1602.05629',
                'extracted_text': (
                    'Modern mobile devices have access to a wealth of data suitable for learning '
                    'models, which in turn can greatly improve the user experience on the device. '
                    'We advocate an alternative that leaves the training data distributed on the '
                    'mobile devices, and learns a shared model by aggregating locally-computed '
                    'updates. We term this decentralized approach Federated Learning.'
                ),
            },
            {
                'title': 'Deep Learning with Differential Privacy',
                'type': 'paper',
                'description': (
                    'Introduces DP-SGD with the moments accountant, enabling practical '
                    'training of deep models with rigorous privacy guarantees.'
                ),
                'authors': 'Abadi, M.; Chu, A.; Goodfellow, I.; McMahan, H. B.; Mironov, I.; Talwar, K.; Zhang, L.',
                'year': '2016',
                'venue': 'Proceedings of the 2016 ACM SIGSAC Conference on Computer and Communications Security',
                'pages': '308-318',
                'doi': '10.1145/2976749.2978318',
                'url': 'https://arxiv.org/abs/1607.00133',
                'extracted_text': (
                    'Machine learning techniques based on neural networks are achieving '
                    'remarkable results in many fields. However, the input data for training '
                    'often contain sensitive information. We develop new algorithmic techniques '
                    'for learning and a refined analysis of privacy costs within the framework '
                    'of differential privacy. Our implementation and experiments demonstrate '
                    'that we can train deep neural networks with non-convex objectives, under a '
                    'modest privacy budget.'
                ),
            },
            {
                'title': 'The 2020 Census Disclosure Avoidance System TopDown Algorithm',
                'type': 'paper',
                'description': (
                    'Documents the US Census Bureau\'s first large-scale deployment of '
                    'differential privacy for official statistics.'
                ),
                'authors': 'Abowd, J. M.; Ashmead, R.; Cumings-Menon, R.; Garfinkel, S.; Heineck, M.; Heiss, C.; Johns, R.; Kifer, D.; Leclerc, P.; Machanavajjhala, A.; Moran, B.; Sexton, W.; Spence, M.; Zhuravlev, P.',
                'year': '2022',
                'venue': 'Harvard Data Science Review',
                'volume': 'Special Issue 2',
                'doi': '10.1162/99608f92.529e3cb9',
                'url': 'https://hdsr.mitpress.mit.edu/pub/7evz361i',
                'extracted_text': (
                    'The US Census Bureau adopted a differentially private disclosure avoidance '
                    'system for the 2020 Census, the first large-scale deployment of differential '
                    'privacy for an official statistical product. The TopDown Algorithm enforces '
                    'invariants and adds calibrated noise across hierarchical geographies.'
                ),
            },
            {
                'title': 'TensorFlow Federated documentation',
                'type': 'link',
                'url': 'https://www.tensorflow.org/federated',
                'description': (
                    'Open-source framework from Google Research for federated computations and '
                    'differentially private aggregation.'
                ),
                'authors': 'Google Research',
                'year': '2024',
                'venue': 'tensorflow.org',
                'extracted_text': (
                    'TensorFlow Federated (TFF) is an open-source framework for machine learning '
                    'and other computations on decentralized data. TFF has been developed to '
                    'facilitate open research and experimentation with Federated Learning, an '
                    'approach to machine learning where a shared global model is trained across '
                    'many participating clients that keep their training data locally.'
                ),
            },
        ],
        'summaries': [
            {
                'title': 'Three complementary privacy techniques',
                'content': (
                    '**Overview**\n'
                    'Federated learning, differential privacy, and homomorphic encryption are '
                    'complementary rather than competing production systems often combine them.\n\n'
                    '**Key Findings**\n'
                    '- FedAvg made on-device training feasible at the scale of millions of '
                    'mobile clients.\n'
                    '- DP-SGD provides formal privacy guarantees at modest accuracy cost; the '
                    'moments accountant gives tight composition bounds.\n'
                    '- The 2020 US Census deployed DP at a scale that previously seemed '
                    'impractical, though small-area accuracy tradeoffs remained controversial.\n\n'
                    '**Implications**\n'
                    'The combination of FL + DP + secure aggregation appears to be the emerging '
                    'production pattern for sensitive applications like keyboard prediction and '
                    'health monitoring.'
                ),
                'cite_indices': [0, 1, 2],
                'styles': ['ieee', 'apa', 'apa'],
            },
        ],
        'comparisons': [
            {
                'title': 'Privacy Techniques in Production',
                'columns': ['Technique', 'Compute Cost', 'Privacy Guarantee', 'Production Use'],
                'rows': ['Federated Learning', 'Differential Privacy', 'Homomorphic Encryption'],
                'cells': [
                    ['Medium (client-side)', 'Empirical', 'Google Gboard, Apple, Meta'],
                    ['Low', 'Mathematical (ε,δ)', 'US Census 2020, Apple iOS analytics'],
                    ['Very High', 'Mathematical', 'Microsoft SEAL, IBM HELib (limited)'],
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed demo accounts, realistic research projects, and social-login config"

    def handle(self, *args, **options):
        #  Sites config 
        site, _ = Site.objects.get_or_create(
            pk=1, defaults={'domain': 'localhost', 'name': 'ResearchDoc'},
        )

        # Seeded so the Google button renders on /login/.
        # Real OAuth requires real credentials set them in
        #   /researchdoc/admin/socialaccount/socialapp/
        for provider, name in [('google', 'Google')]:
            app, _ = SocialApp.objects.get_or_create(
                provider=provider,
                defaults={
                    'name': name,
                    'client_id': 'configure-in-admin',
                    'secret': 'configure-in-admin',
                },
            )
            app.sites.add(site)

        # Demo user
        demo_user, created = User.objects.get_or_create(
            username='aditya6283@gmail.com',
            defaults={'email': 'aditya6283@gmail.com'},
        )
        if created:
            demo_user.set_password('Uq@62833')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS(
                'Created demo user (aditya6283@gmail.com / Uq@62833)'
            ))

        # Update UserDetail (auto-created by signal)
        UserDetail.objects.filter(user=demo_user).update(
            firstname='Demo', surname='Researcher',
            mobile='+61426283405',
            bio='Researcher at UQ',
        )

        # Admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@researchdoc.test',
                password='admin123',
            )
            UserDetail.objects.filter(user=admin).update(
                firstname='Admin', surname='Account',
            )
            self.stdout.write(self.style.SUCCESS(
                'Created admin (admin / admin123)'
            ))

        Subscription.objects.filter(owner=demo_user).update(plan_type='pro')

        sub = Subscription.objects.filter(owner=demo_user).first()
        for data in PROJECTS_DATA:
            project, created = ResearchProject.objects.get_or_create(
                title=data['title'], owner=demo_user,
                defaults={
                    'description': data['description'],
                    'subscription': sub,
                },
            )
            if not created:
                continue

            # Resources
            resources_by_idx = {}
            for i, r in enumerate(data['resources']):
                res = Resource.objects.create(
                    project=project,
                    title=r['title'],
                    description=r['description'],
                    resource_type=r['type'],
                    url=r.get('url', ''),
                    authors=r.get('authors', ''),
                    year=r.get('year', ''),
                    venue=r.get('venue', ''),
                    volume=r.get('volume', ''),
                    issue=r.get('issue', ''),
                    pages=r.get('pages', ''),
                    doi=r.get('doi', ''),
                    extracted_text=r.get('extracted_text', ''),
                )
                resources_by_idx[i] = res

            # Summaries with proper citations in mixed styles
            for s in data['summaries']:
                summ = ResearchSummary.objects.create(
                    project=project, author=demo_user,
                    title=s['title'], content=s['content'],
                )
                cite_indices = s.get('cite_indices', list(resources_by_idx.keys()))
                styles = s.get('styles', [Citation.APA] * len(cite_indices))
                for j, idx in enumerate(cite_indices):
                    if idx in resources_by_idx:
                        res = resources_by_idx[idx]
                        style = styles[j] if j < len(styles) else Citation.APA
                        Citation.objects.create(
                            summary=summ,
                            resource=res,
                            style=style,
                            citation_text=format_citation(res, style)[:1000],
                        )

            # Comparison tables
            for c in data['comparisons']:
                table = ComparisonTable.objects.create(
                    project=project, title=c['title'],
                )
                col_objs = [
                    ComparisonColumn.objects.create(table=table, name=n, order=i)
                    for i, n in enumerate(c['columns'])
                ]
                row_objs = [
                    ComparisonRow.objects.create(table=table, label=l, order=i)
                    for i, l in enumerate(c['rows'])
                ]
                for r_idx, row_vals in enumerate(c['cells']):
                    for c_idx, val in enumerate(row_vals):
                        if c_idx + 1 < len(col_objs):
                            ComparisonCell.objects.create(
                                table=table,
                                row=row_objs[r_idx],
                                column=col_objs[c_idx + 1],
                                value=val,
                            )

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(PROJECTS_DATA)} projects with real bibliographic '
            f'metadata, summaries, citations, and comparison tables.'
        ))
        self.stdout.write('Login credentials:')
        self.stdout.write('  aditya6283@gmail.com / Uq@62833  (regular user)')
        self.stdout.write('  admin / admin123 (superuser)')
        self.stdout.write('')
        self.stdout.write('Social login: SocialApp rows created with placeholders.')
        self.stdout.write('To enable real Google/GitHub login, visit:')
        self.stdout.write('  /researchdoc/admin/socialaccount/socialapp/')
        self.stdout.write('  and replace the client_id and secret values.')
