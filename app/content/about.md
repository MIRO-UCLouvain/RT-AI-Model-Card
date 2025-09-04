## About Model Cards

---

### IMPORTANT INFORMATION, DISCLAIMERS, and FAQs

- This model card aims to **enhance transparency and standardize the reporting of artificial intelligence (AI)-based applications** in the field of **Radiation Therapy**. It is designed for use by professionals in both research and clinical settings to support these objectives. Although it includes items useful for current regulatory requirements, **it does not replace or fulfill regulatory requirements such as the EU Medical Device Regulation or equivalent standards**.
- A **“model”** is defined as the whole set of chained operations that compose an AI-based application. This typically includes a main learning architecture (i.e., with trainable parameters) inserted into a pipeline with pre-processing and post-processing steps. Please note that for safety and transparency purposes, providing information about the full pipeline, including the pre-processing and post-processing steps, is equally important as for the learning architecture itself.
- As a consequence to the model definition above, section 4 of the model card (*Evaluation data, methodology, and results / commissioning*) contains information about the evaluation of the full model pipeline (including pre- and post-processing steps) and not only the learning architecture.
- In order to keep the model card as readable and concise as possible, figures and tables, and other supporting material can be referred to in the information fields and are attached in an **Appendix**.
- **How to deal with changes in the model or in the model card?**

  - *Changes in the card*: In case you want to add or edit information in the card itself (e.g., new evaluation on different dataset, new contact person, new observed limitations, etc), please use the “Versioning” fields (in Card Metadata section) to keep track of the changes from one version to another, and properly indicate the version number.
  - *Changes in the model*: We consider that any change in the model will lead to a new model version and thus a new associated model card. Please use the “Versioning” fields (in Model Basic information section) to keep track of the changes from one model version to another, and properly indicate the version number.
- **Contact:** rtmodelcard@googlegroups.com

We see the model card as a tool to be adapted to the needs of our community, which might change according to the evolution and implementation challenges of AI in Radiation Therapy, both in research and clinical environments. If you would like to propose changes or edits in the model card, please contact our group for further discussion. Also, please indicate any (open source) repository where the model card and/or model are available.

---

### MODEL CARD STRUCTURE

The provided model card is divided into 6 fields:

0) **Card metadata** – Relevant information about the model card itself
1) **Model basic information** – Main information to use the model
2) **Technical specifications** – Model pipeline, learning architecture, software, and hardware
3) **Training data, methodology, and information** – All information about training and validation data
4) **Evaluation data, methodology, and results / commissioning** – All information about the evaluation data and procedure.Because it is common to evaluate your model on a different dataset, this section can be repeated as many times as needed.We refer to **evaluation results** for models that are evaluated but not necessarily with a clinical implementation in mind, and **commissioning** for models that are specifically evaluated within a clinical environment with clinic-specific data.
5) **Other considerations**

**Status of a field:** `*` means **REQUIRED** element. If missing, the element is **OPTIONAL**.


---

### LIST OF AUTHORS

#### CONCEPTION

- **Ana M. Barragán-Montero** — UCLouvain – Institut de Recherche Expérimentale et Clinique, Molecular Imaging Radiotherapy and Oncology (MIRO), Brussels, Belgium
- **Margerie Huet-Dastarac** — UCLouvain – Institut de Recherche Expérimentale et Clinique, Molecular Imaging Radiotherapy and Oncology (MIRO), Brussels, Belgium
- **Benjamin Tengler** — University of Tübingen, Department of Radiation Oncology, Section for Biomedical Physics, Tübingen, Germany
- **Carlos E. Cárdenas** — University of Alabama at Birmingham, Department of Radiation Oncology, Birmingham, AL, USA
- **Marco Fusella** — Radiation Oncology Department, Policlinico Abano Terme, Abano Terme, Italy
- **Geoffroy Herbin** — Ion Beam Applications, Louvain-la-Neuve, Belgium
- **Yvonne de Hond** — Catharina Hospital Eindhoven, Department of Radiation Oncology, Eindhoven, The Netherlands
- **Franziska Knuth** — Erasmus MC Cancer Institute, University Medical Center Rotterdam, Rotterdam, The Netherlands
- **Ciaran Malone** — Department of Medical Physics, St. Luke’s Radiation Oncology Network, Dublin, Ireland
- **Peter van Ooijen** — University of Groningen, University Medical Center Groningen, Department of Radiation Oncology, Groningen, The Netherlands
- **Charlotte Robert** — Department of Radiation Oncology, Gustave Roussy, Villejuif, France
- **Michele Zeverino** — Institute of Radiation Physics, Lausanne University Hospital, Lausanne, Switzerland
- **Coen Hurkmans** — Catharina Hospital Eindhoven, Department of Radiation Oncology, Eindhoven, The Netherlands
- **Tomas Janssen** — Department of Radiation Oncology, The Netherlands Cancer Institute, Amsterdam, The Netherlands
- **Stine Sofia Korreman** — Aarhus University Hospital, Danish Center for Particle Therapy, Aarhus, Denmark
- **Charlotte L. Brouwer** — University of Groningen, University Medical Center Groningen, Department of Radiation Oncology, Groningen, The Netherlands

#### DEVELOPMENT

* **Silvia M. Herranz-Hernández** — UCLouvain – Institut de Recherche Expérimentale et Clinique, Molecular Imaging Radiotherapy and Oncology (MIRO), Brussels, Belgium
