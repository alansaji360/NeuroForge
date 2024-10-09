/*
 * notch.c
 *
 *  Created on: Sep 27, 2024
 *      Author: akarl
 */

#include "notch.h"

void NotchFilterInit(Notch *filt, float centerFreq_Hz, float notchWidth_Hz, float sampleFreq_Hz){

	float sampleTime_s = 1 / sampleFreq_Hz;

	// Converting filter frequencies to angular
	float w0_rps = 2.0 * M_PI * centerFreq_Hz;
	float ww_rps = 2.0 * M_PI * notchWidth_Hz;

	//pre-warp
	float w0_pw_rps = (2.0 / sampleTime_s) * tanf(0.5 * w0_rps * sampleTime_s);

	//calc coeffs
	filt->alpha = 4.0 + w0_pw_rps * w0_pw_rps * sampleTime_s * sampleTime_s;
	filt->beta = 2.0 + ww_rps * sampleTime_s;

	//clear arrays
	filt->x[0] = 0.0; filt->x[1] = 0.0; filt->x[2] = 0.0;
	filt->y[0] = 0.0; filt->y[1] = 0.0; filt->y[2] = 0.0;

}

float NotchFilterUpdate(Notch *filt, float in){

	//shift samples
	filt->x[2] = filt->x[1];
	filt->x[1] = filt->x[0];

	filt->y[2] = filt->y[1];
	filt->y[1] = filt->y[0];

	filt->x[0] = in;

	filt->y[0] = (filt->alpha * filt->x[0] + 2.0 * (filt->alpha - 8.0) * filt->x[1] + filt->alpha * filt->x[2]
				  - (2.0 * (filt->alpha - 8.0) * filt->y[1] + (filt->alpha - filt->beta) * filt->y[2]))
				  / (filt->alpha + filt->beta);

	return filt->y[0] * 20;
}
