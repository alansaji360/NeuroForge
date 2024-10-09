/*
 * EMA.h
 *
 *  Created on: Sep 18, 2024
 *      Author: akarl
 */

#ifndef INC_EMA_H_
#define INC_EMA_H_

typedef struct{
	//filter coefficient (0-1)
	float alpha;

	//filter output
	float out;
} EMA;

void EMA_Init(EMA *filter, float alpha);
void EMA_SetAlpha(EMA *filter, float alpha);
float EMA_Update(EMA *filter, float input);

#endif /* INC_EMA_H_ */
