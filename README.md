3d_image_vis
============

Abstract:

This Project is a test for rendering many images (will be tested on about 40k fukung.net-images) into a 3-Dimensional environment.
Testcase for the 3D-environment will be a Quake3 .map-file which can be converted in Quake3-bsp maps.
Other possible Visualisations are possible as well.

Used Techniques/Libraries:
- OpenCV SURF for extracting Feature-Points out of the images
- OpenCV PCA (manual via Covariance) for clustering
- OpenCV KMeans for finding representants in individual images
- igraph for calculation of the 3D-Representation via Fruchterman-Reingold-3D-Algorithm
- SQLite as Storage

Does it work:

Who knows?! .. Hardest point is the translation into 3D-Coordinates, which needs a nxn-adjacency-Matrix (n images) on which the FR-Algorithm is used.