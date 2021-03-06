import numpy as np
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

def rescaling(z, red, mbin, Mnu):
	
	bcc_final = np.zeros(4)
	for rs in range(len(red)):
		dat_file_path = os.path.join(dir_path, 'coefficients/0.0eV/large_scale/'\
		'LS_z='+str(red[rs])+'_.txt')
		with open(dat_file_path,'r') as f: 
				line = f.readline()   
				bcc_LS000 = float(line.split()[mbin])
				
		
		nu_masses = [0.0, 0.03, 0.06, 0.1, 0.13, 0.15, 0.3, 0.45, 0.6]
		bcc_massive = np.zeros((len(nu_masses)))
		for count, mn in enumerate(nu_masses[1:]):
			dat_file_path2 = os.path.join(dir_path, 'coefficients/other neutrinos masses/'+\
			str(mn)+'eV/LS_z='+str(red[rs])+'_.txt')
			with open(dat_file_path2,'r') as f2: 
				line2 = f2.readline()   
				bcc_massive[count+1] = float(line2.split()[mbin])
				

		bcc_massive[0] = bcc_LS000
		
		# interpolate the bias for the given mass
		bcc_final[rs] = np.interp(Mnu, nu_masses, bcc_massive)/bcc_LS000

	bcc = np.interp(z, red, bcc_final)
	return bcc
