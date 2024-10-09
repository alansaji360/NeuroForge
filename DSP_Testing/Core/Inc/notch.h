/*
 * notch.h
 *
 *  Created on: Sep 27, 2024
 *      Author: akarl
 */

#ifndef INC_NOTCH_H_
#define INC_NOTCH_H_

#include "math.h"

typedef struct {

	//filter coefficients
	float alpha;
	float beta;

	//input and output arrays
	float x[3];
	float y[3];

} Notch;

void NotchFilterInit(Notch *filt, float centerFreq_Hz, float notchWidth_Hz, float sampleFreq_Hz);

float NotchFilterUpdate(Notch *filt, float in);

#endif /* INC_NOTCH_H_ */
