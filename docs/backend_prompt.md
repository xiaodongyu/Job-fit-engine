In the backend, I need to implement the following functions: 
1. parse the resume
1.a: extract text from the pdf of resume 
1.b: parse the text and extract skills, experiences
2. cluster skills and experiences into the following predefined clusters: MLE (machine learning engineer), DS (data scientist), SWE (software engineer), QR (quantitative researcher), QD (quantitative developer). One resume can have one or more clusters, there is no limit on the number of clusters each resume can have but for each cluster that is discovered from a resume, we need provide supporting evidence. 
3. match a resume to a JD (job description) and describe the percentage of matching to each of the cluster in the resume and provide evidence. 
4. if user provides more materials in addition to the resume, these new materislas need to be parse the same as in 1) and 2), and enhance the clusters found from the resume, i.e., add the additional materials to the resume and process them as part of the resume. 