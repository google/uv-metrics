import numpy as np
import torch


class TorchMomentAggregator:

  def __init__(self, max_moment=2):
    self.max_moment = max_moment
    self.shape = None

  def initialize(self, shape):
    self.shape = shape
    self.moments = [torch.zeros(shape) for m in range(self.max_moment)]
    self.count = 0

  def reset(self):
    self.initialize(shape)

  def update(self, sample_measurements):
    # Zeroth dimension is sample dimension
    if self.shape is None:
      self.initialize(sample_measurements.shape[1:])

    for moment in range(self.max_moment):
      self.update_moment(moment, sample_measurements)
    self.update_count(sample_measurements)

  def update_moment(self, moment, sample_measurements):
    with torch.no_grad():
      batch_size = len(sample_measurements)
      batch_avgd_moment = torch.mean(torch.pow(sample_measurements, moment + 1),
                                     axis=0)
      full_count = self.count + batch_size
      full_stat = self.count * self.moments[
          moment] + batch_size * batch_avgd_moment
      self.moments[moment] = full_stat / full_count

  def update_count(self, sample_measurements):
    self.count += len(sample_measurements)

  def get_cumulants(self):
    if self.max_moment > 2:
      raise NotImplementedError(
          'MomentAggregator can only convert moments to cumulants for n<=2')
    elif self.max_moment == 1:
      return self.moments
    elif self.max_moment == 2:
      return [self.moments[0], self.moments[1] - torch.pow(self.moments[0], 2)]
