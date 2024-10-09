/*
 * IIR.h
 *
 *  Created on: Sep 24, 2024
 *      Author: akarl
 */

#ifndef INC_IIR_H_
#define INC_IIR_H_

typedef struct{
	//filter coefficient
	float a[2];
	float b[3];

	//previous in/out
	float x[3];
	float y[2];
	//filter output
	float out;
} IIR2;

void IIR2_Init(IIR2 *filt, float a1,  float a2,  float b1, float b2, float b3);
float IIR2_Update(IIR2 *filt, float input);

typedef struct{
	//filter coefficient (0-1)
	float a[3];
	float b[4];

	//previous in/out
	float x[4];
	float y[3];
	//filter output
	float out;
} IIR3;

void IIR3_Init(IIR3 *filt, float a1,  float a2, float a3, float b1, float b2, float b3, float b4);
float IIR3_Update(IIR3 *filt, float input);

typedef struct{
	//filter coefficient (0-1)
	float a[4];
	float b[5];

	//previous in/out
	float x[5];
	float y[4];
	//filter output
	float out;
} IIR4;

void IIR4_Init(IIR4 *filt, float a1,  float a2, float a3, float a4, float b1, float b2, float b3, float b4, float b5);
float IIR4_Update(IIR4 *filt, float input);

#endif /* INC_IIR_H_ */
