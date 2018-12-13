from classy import Class
from matplotlib.colors import LogNorm
from scipy.interpolate import interp1d
from cimp import cimp
from tuning import tuning
from bcoeff import bcoeff
from ls_coeff import lscoeff
from pt_coeff import ptcoeff
from tnscoeff import tnscoeff
import matplotlib.pyplot as plt
import scipy.constants as const
import math
import error_red
import os
import numpy as np
import warnings
import csv
import sys
from bias import Halo

def rspec(self, cosmo, data, model, case, Massbins, RSD=None, fog=None, err = None):


	####################################################################
    #### Store the redshifts where bcc fit  and bcc Ls are available in arrays
	red2 = [0.0,0.5,1.0,2.0]
	l2= len(red2)
	
	####################################################################
	#### select the k mode according to the ones in Raccanelli et al. 2017
	k_article = [0.35,0.2,0.15]
	
	if case == 1:
		kmax = k_article[0]
	elif case == 2:
		kmax = k_article[1]
	elif case == 3:
		kmax = k_article[2]
		
	####################################################################
	#### import classy results
	redshift, znumber, mv, h, d_tot, T_cb, kclass, pk, f, D = cimp(self, cosmo, data)
	
	####################################################################
	#### compute the fog multipole coefficient if requested
	if fog:
		# get the selected k array
		k, P_halo = Halo(self, cosmo, data, 'lin', case, Massbins)
		kappa = np.zeros((len(k), znumber))
		coeffA = np.zeros((len(k), znumber))
		coeffB = np.zeros((len(k), znumber))
		coeffC = np.zeros((len(k), znumber))
		coeffD = np.zeros((len(k), znumber))
		coeffE = np.zeros((len(k), znumber))

		for iz in xrange(znumber):
			kappa[:,iz] = k*(data.mcmc_parameters['sigma_v']['current']*data.mcmc_parameters['sigma_v']['scale'])*f[iz]*D[iz]
			coeffA[:,iz] = np.arctan(kappa[:,iz]/math.sqrt(2))/(math.sqrt(2)*kappa[:,iz]) + 1/(2+kappa[:,iz]**2)
			coeffB[:,iz] = 6/kappa[:,iz]**2*(coeffA[:,iz] - 2/(2+kappa[:,iz]**2))
			coeffC[:,iz] = -10/kappa[:,iz]**2*(coeffB[:,iz] - 2/(2+kappa[:,iz]**2))
			coeffD[:,iz] = -2/3./kappa[:,iz]**2*(coeffC[:,iz] - 2/(2+kappa[:,iz]**2))
			coeffE[:,iz] = -4/10./kappa[:,iz]**2*(7.*coeffD[:,iz] - 2/(2+kappa[:,iz]**2))
	
	####################################################################
	if model == 'lin':
		# get the fitted ps from p_halo
		k, P_halo = Halo(self, cosmo, data, 'lin', case, Massbins)
		
		# tinker effective bias
		bcc = lscoeff(self,data, mv,Massbins)[1]

		#### get the pt coefficients computed with FAST-PT
		A, B, C, D, E, F, G, H, Pmod_dd, Pmod_dt, Pmod_tt = ptcoeff(self, data, k, Massbins)
		# interpolate on redshift
		k, Pmod_dt = tuning(self, k, Pmod_dt, redshift, znumber, case, Massbins,'2d')
		k, Pmod_tt = tuning(self, k, Pmod_tt, redshift, znumber, case, Massbins,'2d')

		# compute the total matter bias bmm w.r.t bcc using formula 5 in Raccanelli et al.
		bmm = np.zeros((len(kclass),l2, len(Massbins)), 'float64')
		for iz in xrange(l2):
			for count,j in enumerate(Massbins):
				bmm[:,iz, count] = bcc[iz,count] * (T_cb[:,iz]/d_tot[:,iz])
				
		# rescale the k and power spectrum because of classy/class difference
		kclass /= h
		#~ Phh *= h**3
		
		# cut the arrays on selected k and interpolate on z				
		kclass, bmm = tuning(self, kclass, bmm, redshift, znumber, case, Massbins,'3d')
		
		#### load tns coeff
		AB2, AB4, AB6, AB8 = tnscoeff(self, data, model, kclass, Massbins)
		kclass, AB2 = tuning(self, kclass, AB2, redshift, znumber, case, Massbins,'3d')
		kclass, AB4 = tuning(self, kclass, AB4, redshift, znumber, case, Massbins,'3d')
		kclass, AB6 = tuning(self, kclass, AB6, redshift, znumber, case, Massbins,'3d')
		kclass, AB8 = tuning(self, kclass, AB8, redshift, znumber, case, Massbins,'3d')
		
		# compute ps in redshift space
		dim = np.shape(P_halo)
		Pred = np.zeros(dim)
		#------------
		if fog :
			if RSD == 0:
				print 'you chose the Kaiser model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count]*coeffA[:,iz] + 2/3.*bmm[:,iz, count]*f[iz]*coeffB[:,iz] \
						+ 1/5.*f[iz]**2*coeffC[:,iz]
			elif RSD == 1:
				print 'you chose the Scoccimaro model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count]*coeffA[:,iz] + 2/3.*bmm[:,iz, count]*f[iz]*Pmod_dt[:,iz]*coeffB[:,iz] \
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz]*coeffC[:,iz]
			elif RSD == 2:
				print 'you chose the TNS model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count]*coeffA[:,iz] + 2/3.*bmm[:,iz, count]*f[iz]*Pmod_dt[:,iz]*coeffB[:,iz] \
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz]*coeffC[:,iz] + 1/3.*AB2[:,iz,count]*coeffB[:,iz] \
						+ 1/5.*AB4[:,iz,count]*coeffC[:,iz] + 1/7.*AB6[:,iz,count]*coeffD[:,iz] + 1/9.*AB8[:,iz,count]*coeffE[:,iz]
			elif RSD == 3:
				raise ValueError('Not available for the linear model sorry')
		#------------
		else:
			if RSD == 0:
				print 'you chose the Kaiser model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count] + 2/3.*bmm[:,iz, count]*f[iz] + 1/5.*f[iz]**2
			elif RSD == 1:
				print 'you chose the Scoccimaro model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count] + 2/3.*bmm[:,iz, count]*f[iz]*Pmod_dt[:,iz]\
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz]
			elif RSD == 2:
				print 'you chose the TNS model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count]  + 2/3.*bmm[:,iz, count]*f[iz]*Pmod_dt[:,iz]\
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz] + 1/3.*AB2[:,iz,count]+ 1/5.*AB4[:,iz,count]\
						+ 1/7.*AB6[:,iz,count]+ 1/9.*AB8[:,iz,count]
			elif RSD == 3:
				raise ValueError('Not available for the linear model sorry')
			
		# give the error if selected
		if err == True:
			if mv == 0.0 or mv == 0.15:
				error_red.error(self, data, k, Pred, redshift, mv, Massbins)
			else:
				raise ValueError('the simulation spectra are only available for Mv = 0.0 or 0.15eV sorry')

		return k, Pred
		
	#####################################################################
	if model == 'pl':
		# get the fitted ps from p_halo
		k, P_halo = Halo(self, cosmo, data, 'pl', case, Massbins)
		
		# Power law bias
		b1, b2, b3, b4 = bcoeff(self, data, model, case, Massbins)
		
		bcc = np.zeros((len(kclass), l2, len(Massbins)), 'float64')
		for iz in xrange(l2):
			for count,j in enumerate(Massbins):
				#~ ind2 = mbins.index(j)
				bcc[:,iz, count] = b1[iz,count] + b2[iz,count]*(kclass**2) + b3[iz,count]*(kclass**3) \
				+ b4[iz,count]*(kclass**4) 
				
		bcc_LS000 = lscoeff(self,data, mv,Massbins)[0]
		bcc_LSmassive = lscoeff(self,data, mv,Massbins)[1]
		# if mv = 0.0eV bcc_LS000 = bcc_LSmassive
		for iz in xrange(l2):
				for count,j in enumerate(Massbins):
					bcc[:,iz,count] *= bcc_LSmassive[iz,count]/bcc_LS000[iz,count]
		
				
		# compute the total matter bias bmm w.r.t bcc using formula 5 in Raccanelli et al.
		bmm = np.zeros((len(kclass), l2, len(Massbins)), 'float64')
		for iz in xrange(l2):
			for count,j in enumerate(Massbins):
				#~ ind2 = mbins.index(j)
				bmm[:,iz, count] = bcc[:,iz,count] * (T_cb[:,iz]/d_tot[:,iz])


		# rescale the k and power spectrum because of classy/class difference
		kclass /= h
		#~ Phh *= h**3
		
		# cut the arrays on selected k and interpolate on z				
		kclass, bmm = tuning(self, kclass, bmm, redshift, znumber, case, Massbins,'3d')
		
		#### get the pt coefficients computed with FAST-PT
		A, B, C, D, E, F, G, H, Pmod_dd, Pmod_dt, Pmod_tt = ptcoeff(self, data, k, Massbins)
		# interpolate on redshift
		k, Pmod_dt = tuning(self, k, Pmod_dt, redshift, znumber, case, Massbins,'2d')
		k, Pmod_tt = tuning(self, k, Pmod_tt, redshift, znumber, case, Massbins,'2d')
		
		#### load tns coeff
		AB2, AB4, AB6, AB8 = tnscoeff(self, data, model, kclass, Massbins)
		kclass, AB2 = tuning(self, kclass, AB2, redshift, znumber, case, Massbins,'3d')
		kclass, AB4 = tuning(self, kclass, AB4, redshift, znumber, case, Massbins,'3d')
		kclass, AB6 = tuning(self, kclass, AB6, redshift, znumber, case, Massbins,'3d')
		kclass, AB8 = tuning(self, kclass, AB8, redshift, znumber, case, Massbins,'3d')
		
		# compute ps in redshift space
		dim = np.shape(P_halo)
		Pred = np.zeros(dim)
		#------------
		if fog :
			if RSD == 0:
				print 'you chose the Kaiser model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count]*coeffA[:,iz] + 2/3.*bmm[:,iz, count]*f[iz]*coeffB[:,iz] \
						+ 1/5.*f[iz]**2*coeffC[:,iz]
			elif RSD == 1:
				print 'you chose the Scoccimaro model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count]*coeffA[:,iz] + 2/3.*bmm[:,iz, count]*f[iz]*Pmod_dt[:,iz]*coeffB[:,iz] \
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz]*coeffC[:,iz]
			elif RSD == 2:
				print 'you chose the TNS model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count]*coeffA[:,iz] + 2/3.*bmm[:,iz, count]*f[iz]*Pmod_dt[:,iz]*coeffB[:,iz] \
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz]*coeffC[:,iz] + 1/3.*AB2[:,iz,count]*coeffB[:,iz] \
						+ 1/5.*AB4[:,iz,count]*coeffC[:,iz] + 1/7.*AB6[:,iz,count]*coeffD[:,iz] + 1/9.*AB8[:,iz,count]*coeffE[:,iz]
			elif RSD == 3:
				raise ValueError('Not available for the linear model sorry')
		#------------
		else:
			if RSD == 0:
				print 'you chose the Kaiser model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count] + 2/3.*bmm[:,iz, count]*f[iz] + 1/5.*f[iz]**2
			elif RSD == 1:
				print 'you chose the Scoccimaro model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count] + 2/3.*bmm[:,iz, count]*f[iz]*Pmod_dt[:,iz]\
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz]
			elif RSD == 2:
				print 'you chose the TNS model'
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						Pred[:,iz,count] = P_halo[:,iz,count]  + 2/3.*bmm[:,iz, count]*f[iz]*Pmod_dt[:,iz]\
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz] + 1/3.*AB2[:,iz,count]+ 1/5.*AB4[:,iz,count]\
						+ 1/7.*AB6[:,iz,count]+ 1/9.*AB8[:,iz,count]
			elif RSD == 3:
				raise ValueError('Not available for the linear model sorry')
		
		# give the error if selected
		if err == True:
			if mv == 0.0 or mv == 0.15:
				error_red.error(self, data, k, Pred, redshift, mv, Massbins)
			else:
				raise ValueError('the simulation spectra are only available for Mv = 0.0 or 0.15eV sorry')
		
		return k, Pred
		
	#####################################################################
	if model == 'exp':
		# get the fitted ps from p_halo
		k, P_halo = Halo(self, cosmo, data, 'lin', case, Massbins)
		
		# get bias coeff
		b1, b2, bs, b3nl = bcoeff(self, data, model, case, Massbins)
		
		#### get the pt coefficients computed with FAST-PT
		A, B, C, D, E, F, G, H, Pmod_dd, Pmod_dt, Pmod_tt = ptcoeff(self, data, k, Massbins)
		
		#### interpolate t_cb and d_tot on selected k
		#~ np.
		
		# cross velocity spectrum
		PhhDT = np.zeros((len(k),l2,len(Massbins)))
		for iz in xrange(l2):
			for count,j in enumerate(Massbins):
				#~ ind2 = mbins.index(j)
				PhhDT[:,iz,count] = b1[iz,count]* Pmod_dt[:,iz] + b2[iz,count]*G[:,iz] + bs[iz,count]*H[:,iz]\
				+ b3nl[iz,count]*F[:,iz] #*(T_cb[:,iz]/d_tot[:,iz])
		
		bcc_LS000 = lscoeff(self,data, mv,Massbins)[0]
		bcc_LSmassive = lscoeff(self,data, mv,Massbins)[1]
		# if mv = 0.0eV bcc_LS000 = bcc_LSmassive
		for iz in xrange(l2):
				for count,j in enumerate(Massbins):
					PhhDT[:,iz,count] *= bcc_LSmassive[iz,count]/bcc_LS000[iz,count]
		
		# cut the arrays on selected k and interpolate on z				
		k, PhhDT = tuning(self, k, PhhDT, redshift, znumber, case, Massbins,'3d')
		k, Pmod_dt = tuning(self, k, Pmod_dt, redshift, znumber, case, Massbins,'2d')
		k, Pmod_tt = tuning(self, k, Pmod_tt, redshift, znumber, case, Massbins,'2d')
		
		
		#### load tns coeff  and interpolate on z	
		AB2, AB4, AB6, AB8 = tnscoeff(self, data, model, kclass, Massbins)
		# rescale the k and power spectrum because of classy/class difference
		kclass /= h
		kclass, AB2 = tuning(self, kclass, AB2, redshift, znumber, case, Massbins,'3d')
		kclass, AB4 = tuning(self, kclass, AB4, redshift, znumber, case, Massbins,'3d')
		kclass, AB6 = tuning(self, kclass, AB6, redshift, znumber, case, Massbins,'3d')
		kclass, AB8 = tuning(self, kclass, AB8, redshift, znumber, case, Massbins,'3d')
		


		# compute ps in redshift space
		dim = np.shape(P_halo)
		Pred = np.zeros(dim)

		#------------
		if fog :
			if RSD == 0:
				raise ValueError('Not available for the PT expansion model sorry')
			elif RSD == 1:
				raise ValueError('Not available for the PT expansion model sorry')
			elif RSD == 2:
				raise ValueError('Not available for the PT expansion model sorry')
			elif RSD == 3:
				print 'you chose the eTNS model'
				dim = np.shape(P_halo)
				Pred = np.zeros(dim)
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						#~ ind2 = mbins.index(j)
						Pred[:,iz,count] = P_halo[:,iz,count]*coeffA[:,iz]  + 2/3.*f[iz]*PhhDT[:,iz,count]*coeffB[:,iz] \
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz]*coeffC[:,iz] + 1/3.*AB2[:,iz,count]*coeffB[:,iz] \
						+ 1/5.*AB4[:,iz,count]*coeffC[:,iz] + 1/7.*AB6[:,iz,count]*coeffD[:,iz] + 1/9.*AB8[:,iz,count]*coeffE[:,iz]
		#------------
		else:
			if RSD == 0:
				raise ValueError('Not available for the PT expansion model sorry')
			elif RSD == 1:
				raise ValueError('Not available for the PT expansion model sorry')
			elif RSD == 2:
				raise ValueError('Not available for the PT expansion model sorry')
			elif RSD == 3:
				print 'you chose the eTNS model'
				dim = np.shape(P_halo)
				Pred = np.zeros(dim)
				for iz in xrange(znumber):
					for count,j in enumerate(Massbins):
						#~ ind2 = mbins.index(j)
						Pred[:,iz,count] = P_halo[:,iz,count]  + 2/3.*f[iz]*PhhDT[:,iz,count] \
						+ 1/5.*f[iz]**2*Pmod_tt[:,iz] + 1/3.*AB2[:,iz,count]+ 1/5.*AB4[:,iz,count]\
						+ 1/7.*AB6[:,iz,count]+ 1/9.*AB8[:,iz,count]
		
		
		# give the error if selected
		if err == True:
			if mv == 0.0 or mv == 0.15:
				error_red.error(self, data, k, Pred, redshift, mv, Massbins)
			else:
				raise ValueError('the simulation spectra are only available for Mv = 0.0 or 0.15eV sorry')

		return k, Pred