### code written by David Valcin
### for calibration details see arXiv:1901.06045

from interpol import interpol_pt
from coeff import bcoeff
from rescaling import rescaling
from real_ps import real_ps
from power_spec import red_ps
import numpy as np

def ps_calc(coord,kcase, Mnu, mbin, rsd, bmodel, karray, z, fog,  Plin = [] , sigma_v = [] , fz = None, Dz = None):
	print('you chose: ')
	print('- z = '+str(z))
	if coord == 0:
		print('- real space')
	elif coord == 1:
		print('- redshift space')
	print('- Total neutrino mass = ' + str(Mnu)+'eV')
	print('- the mass bin M' + str(mbin +1))
	if rsd == 1:
			print( '- the Kaiser model')
	elif rsd == 2:
			print('- the Scoccimaro model')
	elif rsd == 3:
			print( '- the TNS model')
	if bmodel == 1:
		print('- the linear bias')
	elif bmodel == 2:
		print('- the polynomial bias')
	elif bmodel == 3:
		print('- the perturbation theory bias')
	print ('')
	

	
	# store the calibrated redshift
	red = [0.0,0.5,1.0,2.0] 
	lred = len(red) 
	
	####################################################################
	####################################################################
	### load perturbation terms 

	pt_terms = ['Pmod_dd', 'Pmod_dt', 'Pmod_tt','A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

	Pmod_dd = interpol_pt(pt_terms[0], karray, z, red, lred)
	Pmod_dt = interpol_pt(pt_terms[1], karray, z, red, lred)
	Pmod_tt = interpol_pt(pt_terms[2], karray, z, red, lred)
	A = interpol_pt(pt_terms[3], karray, z, red, lred)
	B = interpol_pt(pt_terms[4], karray, z, red, lred)
	C = interpol_pt(pt_terms[5], karray, z, red, lred)
	D = interpol_pt(pt_terms[6], karray, z, red, lred)
	E = interpol_pt(pt_terms[7], karray, z, red, lred)
	F = interpol_pt(pt_terms[8], karray, z, red, lred)
	G = interpol_pt(pt_terms[9], karray, z, red, lred)
	H = interpol_pt(pt_terms[10], karray, z, red, lred)
	

	
	####################################################################
	####################################################################
	### load bias coefficients
	
	b1, b2, b3, b4 = bcoeff(mbin, bmodel, z, red, lred, kcase)
	
	####################################################################
	####################################################################
	### compute the neutrino rescaling coefficient

	alpha  = rescaling(z, red, mbin, Mnu)
	
	####################################################################
	####################################################################
	### define default parameters
	if Plin == []:
		Plin = Pmod_dd
	if fz == None:
		fvalues = [0.526, 0.760, 0.876, 0.957] #taken from class
		fz = np.interp(z,red,fvalues)
	if Dz == None:
		dvalues = [0.769, 0.607, 0.417, 0.515]#taken from class
		Dz = np.interp(z,red,dvalues)
		
	
	####################################################################
	####################################################################
	### compute the redshift power spectrum
	
	if coord == 0:
		Power = real_ps(mbin, bmodel, karray, b1, b2, b3, b4, A, B, C, D, E, F, G, H, Plin, alpha)
	elif coord == 1:
		Power = red_ps(mbin, bmodel, karray, z, fz, Dz, b1, b2, b3, b4, A, B, C, D, E, F, G, H, Plin,
	Pmod_dt, Pmod_tt, alpha, fog, rsd, red, kcase)

	return Power
