import numpy as np 
import sys,os,h5py,time
import Pk_library as PKL 

################################# INPUT #####################################
redshifts = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 
	1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]

BoxSize = 1000.0 #Mpc/h
#############################################################################

obj = {-1:{'name':'df_cr',  'output':'_',     'axis':0},
	    0:{'name':'df_cs0', 'output':'_RS0_', 'axis':0},
	    1:{'name':'df_cs1', 'output':'_RS1_', 'axis':1},
	    2:{'name':'df_cs2', 'output':'_RS2_', 'axis':2}}

# do a loop over all redshifts
for z in redshifts:

	start = time.time()

	# open files for reading
	f = h5py.File('../density_field_c_z=%.3f.hdf5'%z,'r')
	g = h5py.File('../density_field_n_z=%.3f.hdf5'%z,'r')

	for axis in [-1,0,1,2]:

		# read delta_c
		delta_c = f[obj[axis]['name']][:]
		delta_c /= np.mean(delta_c, dtype=np.float64);  delta_c -= 1.0

		# read delta_n
		delta_n = g[obj[axis]['name']][:]
		delta_n /= np.mean(delta_n, dtype=np.float64);  delta_n -= 1.0

		# compute auto- and cross-Pk
		Pk = PKL.XPk([delta_c, delta_n], BoxSize, axis=obj[axis]['axis'], 
			MAS=['CIC','CIC'], threads=16);  del delta_c, delta_n

		# save results to file
		np.savetxt('Pk_c%sz=%.1f.txt'%(obj[axis]['output'], z), 
			np.transpose([Pk.k3D, Pk.Pk[:,0,0], Pk.Pk[:,1,0], Pk.Pk[:,2,0]]))
		np.savetxt('Pk_n%sz=%.1f.txt'%(obj[axis]['output'], z), 
			np.transpose([Pk.k3D, Pk.Pk[:,0,1], Pk.Pk[:,1,1], Pk.Pk[:,2,1]]))
		np.savetxt('Pk_cn%sz=%.1f.txt'%(obj[axis]['output'], z), 
			np.transpose([Pk.k3D, Pk.XPk[:,0,0], Pk.XPk[:,1,0], Pk.XPk[:,2,0]]))
		del Pk

	f.close();  g.close()
	print 'Redshift %.1f completed: Time taken = %.2f'%(z,time.time()-start)



